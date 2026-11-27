from functools import reduce
from typing import Any, Dict, List, Mapping, Sequence

import attr
import falcon
import pytest
from falcon import testing
from pymongo.database import Database

from ebl.corpus.application.chapter_edit_writer import ChapterEditWriter
from ebl.corpus.domain.chapter import Chapter
from ebl.corpus.domain.chapter_revision import LEGACY_REVISION
from ebl.corpus.domain.word_instances import WordLemma
from ebl.corpus.infrastructure.mongo_text_repository import MongoTextRepository
from ebl.corpus.infrastructure.mongo_text_repository_base import REVISION_FIELD
from ebl.lemmatization.domain.lemmatization import Lemma
from ebl.tests.corpus.line_annotation_assertions import find_changed_paths
from ebl.tests.corpus.line_move_support import STORED_PARSER_VERSION
from ebl.tests.corpus.lines_edit_support import (
    count_chapter_changelog_entries,
    find_stored_chapter,
    read_json,
)
from ebl.tests.corpus.outline_support import dump_outline, remove_key
from ebl.tests.corpus.support import (
    ANY_USER,
    create_chapter_dto,
    create_chapter_url,
    simulate_get,
)
from ebl.tests.corpus.word_instances_reference import (
    find_changed_token_paths,
    lemmatize_instances,
)
from ebl.tests.corpus.word_instances_requests import (
    INSTANCES_QUERY,
    create_count,
    get_instances,
    post_word_lemma,
)
from ebl.tests.corpus.word_instances_support import (
    INSTANCE_LINES,
    NEW_LEMMA,
    NO_INSTANCE_INDICES,
    WORD,
    WORD_COUNT,
)

CHANGED_FIELDS: Sequence[str] = ("lines", REVISION_FIELD)
CHAPTER_VIEW_QUERIES: Sequence[str] = (
    "revision=legacy",
    "view=chapter&revision=legacy",
)
OTHER_NEW_LEMMA: Lemma = NEW_LEMMA[1:]
LEMMA_FIELD = "uniqueLemma"


def find_changed_lemma_paths(
    old: Mapping[str, Any], new: Mapping[str, Any]
) -> List[List[object]]:
    paths = {
        tuple(path[: path.index(LEMMA_FIELD) + 1])
        for path in find_changed_paths(old, new)
    }
    return sorted(map(list, paths), key=str)


def test_every_instance_gets_the_lemma_and_nothing_else_changes(
    client: testing.TestClient,
    text_repository: MongoTextRepository,
    instances_chapter: Chapter,
) -> None:
    stored = text_repository.find_chapter(instances_chapter.id_)
    expected = lemmatize_instances(stored)

    result = post_word_lemma(client, instances_chapter)
    found = text_repository.find_chapter(instances_chapter.id_)

    assert result.status == falcon.HTTP_OK
    assert found.lines == expected.lines
    assert found == expected
    assert found.lines != stored.lines
    assert found.parser_version == STORED_PARSER_VERSION
    assert [found.lines[index] for index in NO_INSTANCE_INDICES] == [
        stored.lines[index] for index in NO_INSTANCE_INDICES
    ]


def test_only_the_lemmas_of_the_instances_change_in_the_stored_document(
    client: testing.TestClient, database: Database, instances_chapter: Chapter
) -> None:
    stored_chapter = find_stored_chapter(database, instances_chapter)

    result = post_word_lemma(client, instances_chapter)
    saved_chapter = find_stored_chapter(database, instances_chapter)

    assert result.status == falcon.HTTP_OK
    assert (
        find_changed_lemma_paths(stored_chapter, saved_chapter)
        == find_changed_token_paths()
    )
    assert reduce(remove_key, CHANGED_FIELDS, saved_chapter) == reduce(
        remove_key, CHANGED_FIELDS, stored_chapter
    )


def test_outline_view_is_the_outline_with_the_new_revision(
    client: testing.TestClient,
    text_repository: MongoTextRepository,
    instances_chapter: Chapter,
) -> None:
    result = post_word_lemma(client, instances_chapter)
    revision = text_repository.find_chapter_revision(instances_chapter.id_)
    outline_result = simulate_get(
        client, create_chapter_url(instances_chapter, "/outline")
    )

    assert result.status == falcon.HTTP_OK
    assert result.json == dump_outline(instances_chapter, revision)
    assert result.json == outline_result.json
    assert revision != LEGACY_REVISION


@pytest.mark.parametrize("query_string", CHAPTER_VIEW_QUERIES)
def test_chapter_view_is_the_lemmatized_chapter(
    client: testing.TestClient, instances_chapter: Chapter, query_string: str
) -> None:
    expected = create_chapter_dto(lemmatize_instances(instances_chapter))

    result = post_word_lemma(client, instances_chapter, query_string)
    chapter_result = simulate_get(client, create_chapter_url(instances_chapter))

    assert result.status == falcon.HTTP_OK
    assert result.json == expected
    assert result.json != create_chapter_dto(instances_chapter)
    assert "revision" not in read_json(result)
    assert chapter_result.json == expected


@pytest.mark.parametrize("query_string", [INSTANCES_QUERY, *CHAPTER_VIEW_QUERIES])
def test_save_writes_one_changelog_entry(
    client: testing.TestClient,
    database: Database,
    instances_chapter: Chapter,
    query_string: str,
) -> None:
    result = post_word_lemma(client, instances_chapter, query_string)

    assert result.status == falcon.HTTP_OK
    assert count_chapter_changelog_entries(database) == 1


def test_every_instance_is_lemmatized_in_the_count_after_the_save(
    client: testing.TestClient, instances_chapter: Chapter
) -> None:
    revision = read_json(post_word_lemma(client, instances_chapter))["revision"]
    parameters: Dict[str, str] = {"word": WORD, "revision": revision}

    result = get_instances(client, instances_chapter, parameters)

    assert result.status == falcon.HTTP_OK
    assert result.json == create_count(
        WORD, WORD_COUNT, WORD_COUNT, INSTANCE_LINES, revision
    )
    assert read_json(result)["lemmatized"] == read_json(result)["words"]


def test_repeating_the_save_at_the_new_revision_is_refused_and_changes_nothing(
    client: testing.TestClient,
    database: Database,
    text_repository: MongoTextRepository,
    instances_chapter: Chapter,
) -> None:
    revision = read_json(post_word_lemma(client, instances_chapter))["revision"]
    stored_chapter = find_stored_chapter(database, instances_chapter)

    result = post_word_lemma(
        client, instances_chapter, f"view=outline&revision={revision}"
    )

    assert result.status == falcon.HTTP_UNPROCESSABLE_ENTITY
    assert read_json(result)["description"] == (
        'Every instance of the word "ana" already has the lemma ana I, ana II. '
        "Nothing was saved."
    )
    assert find_stored_chapter(database, instances_chapter) == stored_chapter
    assert text_repository.find_chapter_revision(instances_chapter.id_) == revision
    assert count_chapter_changelog_entries(database) == 1


def test_saving_another_lemma_at_the_new_revision_replaces_every_lemma(
    client: testing.TestClient,
    database: Database,
    text_repository: MongoTextRepository,
    instances_chapter: Chapter,
) -> None:
    stored = text_repository.find_chapter(instances_chapter.id_)
    first_revision = read_json(post_word_lemma(client, instances_chapter))["revision"]

    result = post_word_lemma(
        client,
        instances_chapter,
        f"view=outline&revision={first_revision}",
        lemma=OTHER_NEW_LEMMA,
    )
    found = text_repository.find_chapter(instances_chapter.id_)

    assert result.status == falcon.HTTP_OK
    assert read_json(result)["revision"] != first_revision
    assert found == lemmatize_instances(stored, OTHER_NEW_LEMMA)
    assert count_chapter_changelog_entries(database) == 2


def test_writer_returns_the_saved_chapter_and_its_revision(
    writer: ChapterEditWriter,
    text_repository: MongoTextRepository,
    instances_chapter: Chapter,
) -> None:
    saved = writer.save_word_lemma(
        instances_chapter.id_, WordLemma(WORD, NEW_LEMMA), LEGACY_REVISION, ANY_USER
    )

    assert saved.chapter == lemmatize_instances(instances_chapter)
    assert saved.chapter == writer.find_chapter(instances_chapter.id_)
    assert saved.revision == text_repository.find_chapter_revision(
        instances_chapter.id_
    )
    assert attr.evolve(saved.chapter, lines=instances_chapter.lines) == (
        instances_chapter
    )
