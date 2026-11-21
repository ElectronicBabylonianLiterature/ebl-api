import json
from typing import Any, Callable, Dict, Sequence, cast

import attr
import falcon
import pytest
from falcon import testing

from ebl.corpus.application.lines_updater import LinesUpdater
from ebl.corpus.domain.chapter import Chapter
from ebl.corpus.domain.chapter_revision import LEGACY_REVISION
from ebl.corpus.domain.lines_update import LinesUpdate
from ebl.corpus.infrastructure.mongo_text_repository import MongoTextRepository
from ebl.dictionary.domain.word import WordId
from ebl.tests.corpus.lines_edit_support import get_lines, post_lines
from ebl.tests.corpus.outline_support import (
    create_chapter_with_lines,
    create_outline_chapter,
    remove_token_fields,
)
from ebl.tests.corpus.support import create_chapter_dto, create_chapter_url
from ebl.tests.factories.corpus import ChapterFactory, LineFactory
from ebl.tests.transliteration.storage_test_helpers import has_key
from ebl.transliteration.application.sign_repository import SignRepository
from ebl.transliteration.domain.line_number import LineNumber
from ebl.transliteration.domain.sign_tokens import Reading
from ebl.transliteration.domain.text_line import TextLine
from ebl.transliteration.domain.word_tokens import Word

LINE_COUNT = 12
LONG_LINE_COUNT = 53
Dto = Dict[str, Any]
INVALID_QUERIES: Sequence[str] = (
    *(f"{key}={value}" for key in ("offset", "limit") for value in ("x", "1.5", "-1")),
    "offset=",
    "offset=2147483648",
    "offset=1&offset=2",
    "limit=0",
    "tokens=yes",
    "tokens=",
)


def create_lemmatized_chapter() -> Chapter:
    lemma = (WordId("aklu I"),)
    word = Word.of([Reading.of_name("ku")], unique_lemma=lemma, alignment=1)
    lemmatized_line = LineFactory.build(
        manuscript_id=1,
        variant__manuscript__line=TextLine.of_iterable(LineNumber(7), [word]),
        variant__manuscript__omitted_words=(),
    )
    lines = (LineFactory.build(manuscript_id=1), lemmatized_line)
    return ChapterFactory.build(lines=lines)


@attr.s(frozen=True, auto_attribs=True)
class LinesPageCase:
    query_string: str
    offset: int
    limit: int
    line_count: int
    tokens: bool


@attr.s(frozen=True, auto_attribs=True)
class RoundTripCase:
    create_chapter: Callable[[], Chapter]
    index: int
    tokens: str


LINES_PAGE_CASES: Sequence[LinesPageCase] = (
    LinesPageCase("", 0, 10, 10, False),
    LinesPageCase("tokens=false", 0, 10, 10, False),
    LinesPageCase("tokens=true", 0, 10, 10, True),
    LinesPageCase("limit=1", 0, 1, 1, False),
    LinesPageCase("offset=3&limit=4", 3, 4, 4, False),
    LinesPageCase("offset=10", 10, 10, 2, False),
    LinesPageCase("offset=9&limit=50&tokens=true", 9, 50, 3, True),
    LinesPageCase("limit=50", 0, 50, 12, False),
    LinesPageCase("offset=12", 12, 10, 0, False),
    LinesPageCase("offset=2147483647&limit=50", 2147483647, 50, 0, False),
)
ROUND_TRIP_CASES: Sequence[RoundTripCase] = (
    RoundTripCase(create_outline_chapter, 0, "false"),
    RoundTripCase(create_outline_chapter, 1, "false"),
    RoundTripCase(create_outline_chapter, 2, "false"),
    RoundTripCase(create_outline_chapter, 0, "true"),
    RoundTripCase(create_lemmatized_chapter, 1, "false"),
    RoundTripCase(create_lemmatized_chapter, 1, "true"),
)


def create_page(chapter: Chapter, offset: int, limit: int, tokens: bool = False) -> Dto:
    lines = create_chapter_dto(chapter)["lines"][offset:][:limit]
    return {
        "total": len(chapter.lines),
        "offset": offset,
        "limit": limit,
        "lines": lines if tokens else [remove_token_fields(line) for line in lines],
        "revision": LEGACY_REVISION,
    }


def get_page(client: testing.TestClient, chapter: Chapter, query_string: str) -> Dto:
    result = get_lines(client, chapter, query_string)
    assert result.status == falcon.HTTP_OK
    return cast(Dto, result.json)


@pytest.fixture
def chapter(text_repository: MongoTextRepository) -> Chapter:
    chapter = create_chapter_with_lines(LINE_COUNT)
    text_repository.create_chapter(chapter)
    return chapter


@pytest.mark.parametrize("case", LINES_PAGE_CASES, ids=str)
def test_get_lines_page(
    client: testing.TestClient, chapter: Chapter, case: LinesPageCase
) -> None:
    page = get_page(client, chapter, case.query_string)

    assert page == create_page(chapter, case.offset, case.limit, case.tokens)
    assert len(page["lines"]) == case.line_count
    assert has_key(page, "reconstructionTokens") is case.tokens
    assert has_key(page, "atfTokens") is case.tokens


@pytest.mark.parametrize(
    "query_string,offset",
    [("limit=51", 0), ("offset=2&limit=1000", 2), ("offset=50&limit=200", 50)],
)
def test_get_lines_page_clamps_limit(
    client: testing.TestClient,
    text_repository: MongoTextRepository,
    query_string: str,
    offset: int,
) -> None:
    long_chapter = create_chapter_with_lines(LONG_LINE_COUNT)
    text_repository.create_chapter(long_chapter)

    page = get_page(client, long_chapter, query_string)

    assert page == create_page(long_chapter, offset, 50)
    assert len(page["lines"]) == min(50, LONG_LINE_COUNT - offset)


def test_get_lines_page_as_guest(
    guest_client: testing.TestClient, chapter: Chapter
) -> None:
    page = get_page(guest_client, chapter, "offset=1&limit=2")

    assert page == create_page(chapter, 1, 2)


def test_get_lines_page_is_not_cached(
    cached_client: testing.TestClient,
    text_repository: MongoTextRepository,
    chapter: Chapter,
) -> None:
    first_page = get_page(cached_client, chapter, "limit=2")
    updated_chapter = attr.evolve(chapter, lines=chapter.lines[1:])
    text_repository.update(chapter.id_, updated_chapter)

    second_page = get_page(cached_client, chapter, "limit=2")
    revision = text_repository.find_chapter_revision(chapter.id_)

    assert first_page == create_page(chapter, 0, 2)
    assert second_page == {**create_page(updated_chapter, 0, 2), "revision": revision}
    assert second_page["total"] == LINE_COUNT - 1
    assert revision != LEGACY_REVISION


@pytest.mark.parametrize("query_string", INVALID_QUERIES)
def test_get_lines_page_with_invalid_query(
    client: testing.TestClient, chapter: Chapter, query_string: str
) -> None:
    url = create_chapter_url(chapter, "/lines")

    result = client.simulate_get(url, query_string=query_string)

    assert result.status == falcon.HTTP_UNPROCESSABLE_ENTITY


@pytest.mark.parametrize(
    "url",
    [
        "/texts/L/1/1/chapters/Standard Babylonian/unknown/lines",
        "/texts/L/1/1/chapters/invalid/any/lines",
        "/texts/L/1/invalid/chapters/Standard Babylonian/any/lines",
    ],
)
def test_get_lines_page_not_found(client: testing.TestClient, url: str) -> None:
    result = client.simulate_get(url)

    assert result.status == falcon.HTTP_NOT_FOUND


@pytest.mark.parametrize("case", ROUND_TRIP_CASES)
def test_posting_a_fetched_line_back_does_not_change_the_chapter(
    client: testing.TestClient,
    text_repository: MongoTextRepository,
    registered_sign_repository: SignRepository,
    store_editable_chapter: Callable[[Chapter], Chapter],
    case: RoundTripCase,
) -> None:
    chapter = store_editable_chapter(case.create_chapter())
    updater = LinesUpdater(LinesUpdate([], set(), {}), registered_sign_repository)
    unchanged_chapter = updater.update(chapter)
    query_string = f"offset={case.index}&limit=1&tokens={case.tokens}"
    page = get_page(client, chapter, query_string)
    edit = {"index": case.index, "line": page["lines"][0]}

    post_result = post_lines(
        client, chapter, json.dumps({"new": [], "deleted": [], "edited": [edit]}), ""
    )
    revision = text_repository.find_chapter_revision(chapter.id_)

    assert post_result.status == falcon.HTTP_OK
    assert post_result.json == create_chapter_dto(unchanged_chapter)
    assert text_repository.find_chapter(chapter.id_).lines == unchanged_chapter.lines
    assert get_page(client, chapter, "limit=50") == {
        **create_page(chapter, 0, 50),
        "revision": revision,
    }
    assert revision != LEGACY_REVISION
