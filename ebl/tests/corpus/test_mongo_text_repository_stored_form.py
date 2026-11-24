from typing import Any, Callable, Dict, List, cast

import attr
import pytest
from pymongo.database import Database

from ebl.corpus.application.schemas import LineSchema
from ebl.corpus.domain.chapter import Chapter
from ebl.corpus.domain.chapter_change import ChapterChange
from ebl.corpus.domain.line_layout import LineLayout
from ebl.corpus.infrastructure.mongo_text_repository import MongoTextRepository
from ebl.corpus.infrastructure.queries import chapter_id_query
from ebl.tests.corpus.chapter_change_support import (
    FIRST_EDITED_NUMBER,
    FIRST_NEW_NUMBER,
    edit_line,
)
from ebl.tests.corpus.line_annotation_support import replace_item
from ebl.tests.corpus.line_move_support import LINE_COUNT, create_move_chapter
from ebl.tests.corpus.lines_edit_support import find_stored_chapter
from ebl.tests.corpus.literal_content_support import (
    DOLLAR_NOTE,
    DOLLAR_NOTES,
    DOLLAR_PARATEXT,
    DOLLAR_PREFIX,
    DOLLAR_RECONSTRUCTION,
    DOLLAR_SIGNS,
    DOLLAR_TEXT,
    DOLLAR_TRANSLATION,
    DOLLAR_VERSION,
    SERVER_KEYS,
    add_dollar_fields,
    create_dollar_line,
)
from ebl.tests.corpus.reference_save_support import (
    ChapterCopies,
    find_comparable_chapter,
)
from ebl.tests.transliteration.storage_test_helpers import stored_dump
from ebl.transliteration.domain.line_number import LineNumber, LineNumberRange
from ebl.transliteration.infrastructure.collections import CHAPTERS_COLLECTION

EDITED_INDEX = 0
DOLLAR_INDEXES = (0, 2)
UNKNOWN_FIELD_INDEX = 1
MISSING_FIELD_INDEX = 2
OLD_FORM_INDEXES = (UNKNOWN_FIELD_INDEX, MISSING_FIELD_INDEX)
UNKNOWN_FIELD = "legacyField"
OPTIONAL_FIELD = "oldLineNumbers"
OLD_FORM_UPDATE = {
    "$set": {f"lines.{UNKNOWN_FIELD_INDEX}.number.start.{UNKNOWN_FIELD}": 7},
    "$unset": {f"lines.{MISSING_FIELD_INDEX}.{OPTIONAL_FIELD}": ""},
}
RANGE = LineNumberRange(LineNumber(20), LineNumber(21))


@pytest.fixture
def chapter(store_editable_chapter: Callable[[Chapter], Chapter]) -> Chapter:
    chapter = create_move_chapter()
    return store_editable_chapter(
        attr.evolve(
            chapter,
            lines=replace_item(
                chapter.lines,
                UNKNOWN_FIELD_INDEX,
                attr.evolve(chapter.lines[UNKNOWN_FIELD_INDEX], number=RANGE),
            ),
        )
    )


def create_dollar_change(chapter: Chapter) -> ChapterChange:
    edited_line = attr.evolve(
        create_dollar_line(FIRST_EDITED_NUMBER), number=chapter.lines[0].number
    )
    return ChapterChange(
        chapter,
        add_dollar_fields(
            attr.evolve(
                chapter,
                lines=(
                    edited_line,
                    chapter.lines[1],
                    create_dollar_line(FIRST_NEW_NUMBER),
                    *chapter.lines[2:],
                ),
            )
        ),
        LineLayout((0, 1, None, 2, 3)),
    )


def find_strings(value: object) -> List[str]:
    if isinstance(value, dict):
        return [string for item in value.values() for string in find_strings(item)]
    if isinstance(value, list):
        return [string for item in value for string in find_strings(item)]
    return [value] if isinstance(value, str) else []


def test_strings_that_look_like_field_paths_are_stored_as_they_are(
    database: Database, copies: ChapterCopies, chapter: Chapter
) -> None:
    change = create_dollar_change(chapter)

    copies.assert_updates_like_the_full_update(change)
    stored_chapter = find_stored_chapter(database, chapter)
    strings = find_strings(stored_chapter["lines"][0])

    assert stored_chapter["signs"] == list(DOLLAR_SIGNS)
    assert stored_chapter["parserVersion"] == DOLLAR_VERSION
    assert stored_chapter["uncertainFragments"] == [
        {"prefix": "$K", "number": "$1", "suffix": ""}
    ]
    assert [manuscript["notes"] for manuscript in stored_chapter["manuscripts"]] == [
        DOLLAR_NOTES,
        DOLLAR_NOTES,
    ]
    assert [stored_chapter["lines"][index] for index in DOLLAR_INDEXES] == [
        stored_dump(LineSchema(), change.new.lines[index]) for index in DOLLAR_INDEXES
    ]
    assert {
        DOLLAR_TRANSLATION,
        DOLLAR_NOTE,
        DOLLAR_PARATEXT,
        DOLLAR_TEXT,
        DOLLAR_RECONSTRUCTION,
        DOLLAR_PREFIX,
    } <= set(strings)
    assert stored_chapter["lines"][0]["variants"][1]["manuscripts"] == []


def test_keys_that_look_like_operators_and_paths_are_stored_as_they_are(
    database: Database,
    copies: ChapterCopies,
    chapter: Chapter,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    dump = LineSchema.dump
    sibling = copies.create_sibling(chapter)
    change = create_dollar_change(chapter)

    def add_keys(line: Dict[str, Any]) -> Dict[str, Any]:
        return {**line, **SERVER_KEYS}

    def dump_with_server_keys(
        schema: LineSchema, value: object, **kwargs: bool
    ) -> object:
        dumped = dump(schema, value, **kwargs)
        return (
            [add_keys(line) for line in cast(List[Dict[str, Any]], dumped)]
            if isinstance(dumped, list)
            else add_keys(cast(Dict[str, Any], dumped))
        )

    monkeypatch.setattr(LineSchema, "dump", dump_with_server_keys)
    copies.update(change)
    copies.update_fully(sibling, change.new)
    monkeypatch.undo()
    saved = find_comparable_chapter(database, chapter)
    fully_saved = find_comparable_chapter(database, sibling)

    assert [
        {key: line[key] for key in SERVER_KEYS if key in line}
        for line in saved["lines"]
    ] == [SERVER_KEYS, {}, SERVER_KEYS, {}, {}]
    assert [saved["lines"][index] for index in DOLLAR_INDEXES] == [
        fully_saved["lines"][index] for index in DOLLAR_INDEXES
    ]
    assert {**saved, "lines": fully_saved["lines"]} == fully_saved


def test_unchanged_lines_keep_their_stored_form(
    database: Database,
    text_repository: MongoTextRepository,
    copies: ChapterCopies,
    chapter: Chapter,
) -> None:
    sibling = copies.create_sibling(chapter)
    database[CHAPTERS_COLLECTION].update_many({}, OLD_FORM_UPDATE)
    stored_lines = find_stored_chapter(database, chapter)["lines"]
    stored_raw_lines = copies.find_raw_lines(chapter)
    loaded = text_repository.find_chapter(chapter.id_)
    edited_line = edit_line(loaded.lines[EDITED_INDEX], FIRST_EDITED_NUMBER)
    change = ChapterChange.in_place(
        loaded, attr.evolve(loaded, lines=(edited_line, *loaded.lines[1:]))
    )

    copies.update(change)
    copies.update_fully(sibling, change.new)
    saved = find_comparable_chapter(database, chapter)
    fully_saved = find_comparable_chapter(database, sibling)

    assert copies.find_raw_lines(chapter)[1:] == stored_raw_lines[1:]
    assert saved["lines"][EDITED_INDEX] == fully_saved["lines"][EDITED_INDEX]
    assert saved["lines"][EDITED_INDEX] != stored_lines[EDITED_INDEX]
    assert [
        index
        for index in range(LINE_COUNT)
        if saved["lines"][index] != fully_saved["lines"][index]
    ] == list(OLD_FORM_INDEXES)
    assert {**saved, "lines": fully_saved["lines"]} == fully_saved
    assert text_repository.find_chapter(chapter.id_) == attr.evolve(
        text_repository.find_chapter(sibling.id_), name=chapter.name
    )


def test_stored_forms_of_the_test_are_old_forms(
    database: Database, text_repository: MongoTextRepository, chapter: Chapter
) -> None:
    stored_lines = find_stored_chapter(database, chapter)["lines"]

    database[CHAPTERS_COLLECTION].update_one(
        chapter_id_query(chapter.id_), OLD_FORM_UPDATE
    )
    old_lines = find_stored_chapter(database, chapter)["lines"]
    text_repository.update(chapter.id_, text_repository.find_chapter(chapter.id_))

    assert OPTIONAL_FIELD in stored_lines[MISSING_FIELD_INDEX]
    assert [
        index for index in range(LINE_COUNT) if old_lines[index] != stored_lines[index]
    ] == list(OLD_FORM_INDEXES)
    assert find_stored_chapter(database, chapter)["lines"] == stored_lines
