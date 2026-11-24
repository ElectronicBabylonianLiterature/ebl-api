import json
from typing import Callable, Sequence

import falcon
import pytest
from falcon import testing
from pymongo.database import Database

from ebl.cache.infrastructure.mongo_cache_repository import COLLECTION
from ebl.corpus.application.lemmatization_updater import LemmatizationUpdater
from ebl.corpus.domain.chapter import Chapter
from ebl.corpus.infrastructure.mongo_text_repository import MongoTextRepository
from ebl.tests.corpus.chapter_edit_support import ChapterEditRequest, post_edit
from ebl.tests.corpus.line_annotation_kinds import dump_lemmatization
from ebl.tests.corpus.lines_edit_support import (
    STALE_REVISION,
    count_chapter_changelog_entries,
    read_json,
)
from ebl.tests.corpus.support import (
    create_chapter_dto,
    create_chapter_url,
    dump_line_details,
    simulate_get,
)
from ebl.tests.corpus.word_instances_reference import (
    create_chapter_lemmatization,
    lemmatize_instances,
)
from ebl.tests.corpus.word_instances_requests import (
    INSTANCES_QUERY,
    INSTANCES_SUFFIX,
    create_word_lemma_request,
    post_word_lemma,
)
from ebl.tests.corpus.word_instances_support import (
    INSTANCE_LINES,
    MOVE_CHAPTER_WORD,
    NEW_LEMMA,
    WORD,
)

LEMMATIZATION_SUFFIX = "/lemmatization"
OTHER_WORD = "eliš"
CACHED_LINE = INSTANCE_LINES[0]
CACHED_SUFFIXES: Sequence[str] = ("/display", f"/lines/{CACHED_LINE}")
UNROUTED_SUFFIXES: Sequence[str] = (
    "/lemmatization/instances/0",
    "/lemmatization/instances/ana",
    "/lemmatization/instance",
    "/lemmatization/0",
    "/lemmatization/0/instances",
    "/instances",
)
OTHER_METHODS: Sequence[str] = ("PUT", "PATCH", "DELETE", "HEAD")
MIXED_FIELDS: Sequence[str] = ("lemmatization", "uniqueLemma", "word")
IGNORED_QUERIES: Sequence[str] = ("", f"view=outline&revision={STALE_REVISION}")


def create_lemmatization_request(chapter: Chapter, word: str) -> ChapterEditRequest:
    lemmatization = [
        dump_lemmatization(tuple(line))
        for line in create_chapter_lemmatization(chapter, word)
    ]
    return ChapterEditRequest(
        LEMMATIZATION_SUFFIX, json.dumps({"lemmatization": lemmatization})
    )


def lemmatize_chapter(chapter: Chapter, word: str) -> Chapter:
    return LemmatizationUpdater(create_chapter_lemmatization(chapter, word)).update(
        chapter
    )


@pytest.mark.parametrize("query_string", IGNORED_QUERIES)
def test_chapter_lemmatization_route_saves_the_whole_lemmatization_as_before(
    client: testing.TestClient,
    database: Database,
    text_repository: MongoTextRepository,
    annotation_chapter: Chapter,
    query_string: str,
) -> None:
    expected = lemmatize_chapter(annotation_chapter, MOVE_CHAPTER_WORD)
    request = create_lemmatization_request(annotation_chapter, MOVE_CHAPTER_WORD)

    result = post_edit(client, annotation_chapter, request, query_string)

    assert result.status == falcon.HTTP_OK
    assert result.json == create_chapter_dto(expected)
    assert result.json != create_chapter_dto(annotation_chapter)
    assert "revision" not in read_json(result)
    assert text_repository.find_chapter(annotation_chapter.id_).lines == expected.lines
    assert count_chapter_changelog_entries(database) == 1


def test_both_lemmatization_saves_reach_their_own_resource(
    client: testing.TestClient,
    text_repository: MongoTextRepository,
    annotation_chapter: Chapter,
) -> None:
    lemmatized_chapter = lemmatize_chapter(annotation_chapter, MOVE_CHAPTER_WORD)
    expected = lemmatize_chapter(lemmatized_chapter, OTHER_WORD)

    instances_result = post_word_lemma(
        client, annotation_chapter, word=MOVE_CHAPTER_WORD
    )
    result = post_edit(
        client,
        annotation_chapter,
        create_lemmatization_request(lemmatized_chapter, OTHER_WORD),
        "",
    )

    assert instances_result.status == falcon.HTTP_OK
    assert "revision" in read_json(instances_result)
    assert result.status == falcon.HTTP_OK
    assert result.json == create_chapter_dto(expected)
    assert text_repository.find_chapter(annotation_chapter.id_).lines == expected.lines
    assert expected.lines != lemmatized_chapter.lines != annotation_chapter.lines


def test_posting_the_word_lemma_to_the_chapter_lemmatization_route_is_refused(
    client: testing.TestClient,
    instances_chapter: Chapter,
    assert_instances_unchanged: Callable[[], None],
) -> None:
    body = create_word_lemma_request(WORD, list(NEW_LEMMA)).body
    request = ChapterEditRequest(LEMMATIZATION_SUFFIX, body)

    result = post_edit(client, instances_chapter, request, INSTANCES_QUERY)

    assert result.status == falcon.HTTP_BAD_REQUEST
    assert sorted(read_json(result)["description"]) == list(MIXED_FIELDS)
    assert_instances_unchanged()


def test_posting_the_chapter_lemmatization_to_the_instances_route_is_refused(
    client: testing.TestClient,
    instances_chapter: Chapter,
    assert_instances_unchanged: Callable[[], None],
) -> None:
    body = create_lemmatization_request(instances_chapter, OTHER_WORD).body
    request = ChapterEditRequest(INSTANCES_SUFFIX, body)

    result = post_edit(client, instances_chapter, request, INSTANCES_QUERY)

    assert result.status == falcon.HTTP_BAD_REQUEST
    assert sorted(read_json(result)["description"]) == list(MIXED_FIELDS)
    assert_instances_unchanged()


@pytest.mark.parametrize("query_string", ["", "word=ana"])
def test_getting_the_chapter_lemmatization_route_is_not_allowed(
    client: testing.TestClient, instances_chapter: Chapter, query_string: str
) -> None:
    result = client.simulate_get(
        create_chapter_url(instances_chapter, LEMMATIZATION_SUFFIX),
        query_string=query_string,
    )

    assert result.status == falcon.HTTP_METHOD_NOT_ALLOWED
    assert result.headers["allow"] == "POST, OPTIONS"


@pytest.mark.parametrize("method", OTHER_METHODS)
def test_other_methods_on_the_instances_route_are_not_allowed(
    client: testing.TestClient,
    instances_chapter: Chapter,
    assert_instances_unchanged: Callable[[], None],
    method: str,
) -> None:
    result = client.simulate_request(
        method,
        create_chapter_url(instances_chapter, INSTANCES_SUFFIX),
        body=create_word_lemma_request(WORD, list(NEW_LEMMA)).body,
        query_string=f"word={WORD}&{INSTANCES_QUERY}",
    )

    assert result.status == falcon.HTTP_METHOD_NOT_ALLOWED
    assert result.headers["allow"] == "GET, POST, OPTIONS"
    assert_instances_unchanged()


@pytest.mark.parametrize("suffix", UNROUTED_SUFFIXES)
def test_other_paths_are_not_routed(
    client: testing.TestClient,
    instances_chapter: Chapter,
    assert_instances_unchanged: Callable[[], None],
    suffix: str,
) -> None:
    request = ChapterEditRequest(
        suffix, create_word_lemma_request(WORD, list(NEW_LEMMA)).body
    )

    post_result = post_edit(client, instances_chapter, request, INSTANCES_QUERY)
    get_result = simulate_get(
        client, f"{create_chapter_url(instances_chapter, suffix)}?word={WORD}"
    )

    assert post_result.status == falcon.HTTP_NOT_FOUND
    assert get_result.status == falcon.HTTP_NOT_FOUND
    assert_instances_unchanged()


def test_save_invalidates_the_cached_displays(
    client: testing.TestClient,
    database: Database,
    store_text: Callable[[Chapter], Chapter],
    instances_chapter: Chapter,
) -> None:
    chapter = store_text(instances_chapter)
    endpoints = [create_chapter_url(chapter, suffix) for suffix in CACHED_SUFFIXES]
    cached_display, cached_line = (
        simulate_get(client, endpoint) for endpoint in endpoints
    )
    cached_count = database[COLLECTION].count_documents({})

    result = post_word_lemma(client, chapter)
    count_after_save = database[COLLECTION].count_documents({})
    display, line = (simulate_get(client, endpoint) for endpoint in endpoints)

    assert result.status == falcon.HTTP_OK
    assert cached_count == len(endpoints)
    assert count_after_save == 0
    assert display.json != cached_display.json
    assert line.json == dump_line_details(lemmatize_instances(chapter), CACHED_LINE)
    assert line.json != cached_line.json
    assert database[COLLECTION].count_documents({}) == len(endpoints)
