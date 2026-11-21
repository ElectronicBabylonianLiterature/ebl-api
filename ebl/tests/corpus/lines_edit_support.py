import json
from typing import Any, Dict, List, cast

import attr
from falcon import testing
from pymongo.database import Database

from ebl.corpus.application.corpus import COLLECTION
from ebl.corpus.domain.chapter import Chapter
from ebl.corpus.domain.lines_update import LinesUpdate
from ebl.corpus.infrastructure.queries import chapter_id_query
from ebl.tests.corpus.support import create_chapter_dto, create_chapter_url
from ebl.transliteration.domain.atf import ATF_PARSER_VERSION
from ebl.transliteration.domain.line_number import LineNumber
from ebl.transliteration.infrastructure.collections import CHAPTERS_COLLECTION

EDITED_INDEX = 2
EDITED_NUMBER = LineNumber(9, True)
OTHER_EDITED_NUMBER = LineNumber(8, True)
STALE_REVISION = "0123456789abcdef01234567"
CHANGELOG_COLLECTION = "changelog"
LINES_SUFFIX = "/lines"


def update_chapter(
    chapter: Chapter, index: int, number: LineNumber = EDITED_NUMBER
) -> Chapter:
    edited_line = attr.evolve(
        chapter.lines[index],
        number=number,
        is_beginning_of_section=not chapter.lines[index].is_beginning_of_section,
    )
    return attr.evolve(
        chapter,
        lines=tuple(
            (edited_line if line_index == index else line).set_variant_alignment_flags()
            for line_index, line in enumerate(chapter.lines)
        ),
        parser_version=ATF_PARSER_VERSION,
    )


def create_lines_update(updated_chapter: Chapter, index: int) -> LinesUpdate:
    return LinesUpdate([], set(), {index: updated_chapter.lines[index]})


def create_body(updated_chapter: Chapter, index: int) -> str:
    line = create_chapter_dto(updated_chapter)["lines"][index]
    return json.dumps(
        {"new": [], "deleted": [], "edited": [{"index": index, "line": line}]}
    )


def post_lines(
    client: testing.TestClient, chapter: Chapter, body: str, query_string: str
) -> testing.Result:
    result = client.simulate_post(
        create_chapter_url(chapter, LINES_SUFFIX),
        body=body,
        query_string=query_string,
    )
    assert isinstance(result, testing.Result)
    return result


def get_lines(
    client: testing.TestClient, chapter: Chapter, query_string: str
) -> testing.Result:
    result = client.simulate_get(
        create_chapter_url(chapter, LINES_SUFFIX), query_string=query_string
    )
    assert isinstance(result, testing.Result)
    return result


def read_json(result: testing.Result) -> Dict[str, Any]:
    return cast(Dict[str, Any], result.json)


def count_chapter_changelog_entries(database: Database) -> int:
    return database[CHANGELOG_COLLECTION].count_documents({"resource_type": COLLECTION})


def find_chapter_changelog_entries(database: Database) -> List[Dict[str, Any]]:
    return list(
        database[CHANGELOG_COLLECTION].find({"resource_type": COLLECTION}).sort("_id")
    )


def find_stored_chapter(database: Database, chapter: Chapter) -> Dict[str, Any]:
    stored_chapter = database[CHAPTERS_COLLECTION].find_one(
        chapter_id_query(chapter.id_)
    )
    assert stored_chapter is not None
    return stored_chapter
