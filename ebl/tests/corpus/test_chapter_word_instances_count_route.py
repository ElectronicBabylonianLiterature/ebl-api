from typing import Callable, Dict, Sequence, Tuple

import attr
import falcon
import pytest
from falcon import testing

from ebl.corpus.domain.chapter import Chapter
from ebl.corpus.domain.chapter_revision import (
    LEGACY_REVISION,
    chapter_revision_conflict,
)
from ebl.corpus.infrastructure.mongo_text_repository import MongoTextRepository
from ebl.tests.corpus.lines_edit_support import STALE_REVISION, read_json
from ebl.tests.corpus.support import create_chapter_url, simulate_get
from ebl.tests.corpus.word_instances_reference import lemmatize_instances
from ebl.tests.corpus.word_instances_requests import (
    INSTANCES_SUFFIX,
    create_count,
    get_instances,
)
from ebl.tests.corpus.word_instances_support import (
    COUNT_CASES,
    INSTANCE_LINES,
    LEMMATIZED_COUNT,
    WORD,
    WORD_COUNT,
    CountCase,
)

INVALID_WORD = "word must be a non-empty string, got {} instead"
INVALID_WORD_QUERIES: Sequence[Tuple[str, str]] = (
    ("", "word is required"),
    ("revision=legacy", "word is required"),
    ("words=ana", "word is required"),
    ("word=", INVALID_WORD.format("''")),
    ("word=&revision=legacy", INVALID_WORD.format("''")),
    ("word=ana&word=ana", INVALID_WORD.format("['ana', 'ana']")),
)
INVALID_REVISION_QUERIES: Sequence[str] = (
    "word=ana&revision=",
    "word=ana&revision=a&revision=b",
)


def update_chapter(text_repository: MongoTextRepository, chapter: Chapter) -> str:
    text_repository.update(chapter.id_, lemmatize_instances(chapter))
    return text_repository.find_chapter_revision(chapter.id_)


def get_with_query(
    client: testing.TestClient, chapter: Chapter, query_string: str
) -> testing.Result:
    return simulate_get(
        client, f"{create_chapter_url(chapter, INSTANCES_SUFFIX)}?{query_string}"
    )


@pytest.mark.parametrize("case", COUNT_CASES, ids=lambda case: case[0])
def test_counting_the_instances_of_a_word(
    client: testing.TestClient, instances_chapter: Chapter, case: CountCase
) -> None:
    word, words, lemmatized, lines = case

    result = get_instances(client, instances_chapter, {"word": word})

    assert result.status == falcon.HTTP_OK
    assert result.json == create_count(word, words, lemmatized, lines)


def test_count_of_the_word_in_reconstructions_manuscripts_and_variants(
    client: testing.TestClient, instances_chapter: Chapter
) -> None:
    result = get_instances(client, instances_chapter, {"word": WORD})

    assert result.json == {
        "word": "ana",
        "words": 8,
        "lemmatized": 5,
        "lines": [1, 4, 5],
        "revision": "legacy",
    }
    assert result.json == create_count(
        WORD, WORD_COUNT, LEMMATIZED_COUNT, INSTANCE_LINES
    )


def test_counting_as_guest(
    guest_client: testing.TestClient, instances_chapter: Chapter
) -> None:
    result = get_instances(guest_client, instances_chapter, {"word": WORD})

    assert result.status == falcon.HTTP_OK
    assert read_json(result)["words"] == WORD_COUNT


def test_count_is_not_cached(
    cached_client: testing.TestClient,
    text_repository: MongoTextRepository,
    instances_chapter: Chapter,
) -> None:
    first_result = get_instances(cached_client, instances_chapter, {"word": WORD})
    revision = update_chapter(text_repository, instances_chapter)

    second_result = get_instances(cached_client, instances_chapter, {"word": WORD})

    assert read_json(first_result)["lemmatized"] == LEMMATIZED_COUNT
    assert second_result.json == create_count(
        WORD, WORD_COUNT, WORD_COUNT, INSTANCE_LINES, revision
    )
    assert revision != LEGACY_REVISION


def test_counting_at_the_legacy_revision(
    client: testing.TestClient, instances_chapter: Chapter
) -> None:
    parameters: Dict[str, str] = {"word": WORD, "revision": LEGACY_REVISION}

    result = get_instances(client, instances_chapter, parameters)

    assert result.status == falcon.HTTP_OK
    assert result.json == get_instances(client, instances_chapter, {"word": WORD}).json


def test_counting_at_the_current_revision(
    client: testing.TestClient,
    text_repository: MongoTextRepository,
    instances_chapter: Chapter,
) -> None:
    revision = update_chapter(text_repository, instances_chapter)

    result = get_instances(
        client, instances_chapter, {"word": WORD, "revision": revision}
    )

    assert result.status == falcon.HTTP_OK
    assert read_json(result)["revision"] == revision


@pytest.mark.parametrize("stale_revision", [STALE_REVISION, LEGACY_REVISION])
def test_counting_at_a_stale_revision(
    client: testing.TestClient,
    text_repository: MongoTextRepository,
    instances_chapter: Chapter,
    stale_revision: str,
) -> None:
    revision = update_chapter(text_repository, instances_chapter)
    conflict = chapter_revision_conflict(
        instances_chapter.id_, stale_revision, revision
    )

    result = get_instances(
        client, instances_chapter, {"word": WORD, "revision": stale_revision}
    )

    assert result.status == falcon.HTTP_CONFLICT
    assert read_json(result)["description"] == str(conflict)


def test_counting_in_a_never_updated_chapter_at_a_stale_revision(
    guest_client: testing.TestClient, instances_chapter: Chapter
) -> None:
    result = get_instances(
        guest_client, instances_chapter, {"word": "missing", "revision": STALE_REVISION}
    )

    assert result.status == falcon.HTTP_CONFLICT


@pytest.mark.parametrize("invalid_query", INVALID_WORD_QUERIES)
def test_counting_without_a_valid_word(
    client: testing.TestClient,
    instances_chapter: Chapter,
    invalid_query: Tuple[str, str],
) -> None:
    query_string, description = invalid_query

    result = get_with_query(client, instances_chapter, query_string)

    assert result.status == falcon.HTTP_UNPROCESSABLE_ENTITY
    assert read_json(result)["description"] == description


@pytest.mark.parametrize("query_string", INVALID_REVISION_QUERIES)
def test_counting_with_an_invalid_revision(
    client: testing.TestClient, instances_chapter: Chapter, query_string: str
) -> None:
    result = get_with_query(client, instances_chapter, query_string)

    assert result.status == falcon.HTTP_UNPROCESSABLE_ENTITY


@pytest.mark.parametrize("revision", [LEGACY_REVISION, STALE_REVISION])
def test_counting_in_an_unknown_chapter(
    client: testing.TestClient, instances_chapter: Chapter, revision: str
) -> None:
    missing_chapter = attr.evolve(
        instances_chapter, name=f"{instances_chapter.name} missing"
    )

    result = get_instances(
        client, missing_chapter, {"word": WORD, "revision": revision}
    )

    assert result.status == falcon.HTTP_NOT_FOUND


@pytest.mark.parametrize(
    "url",
    [
        "/texts/L/1/1/chapters/invalid/any/lemmatization/instances",
        "/texts/L/1/invalid/chapters/Standard Babylonian/any/lemmatization/instances",
    ],
)
def test_counting_in_an_invalid_chapter(client: testing.TestClient, url: str) -> None:
    result = simulate_get(client, f"{url}?word=ana")

    assert result.status == falcon.HTTP_NOT_FOUND


def test_counting_does_not_change_the_chapter(
    client: testing.TestClient,
    instances_chapter: Chapter,
    assert_instances_unchanged: Callable[[], None],
) -> None:
    result = get_instances(client, instances_chapter, {"word": WORD})

    assert result.status == falcon.HTTP_OK
    assert_instances_unchanged()
