import json
from typing import Any, Callable, Dict, List, Sequence, cast

import attr
import falcon
import pytest
from falcon import testing

from ebl.bibliography.application.bibliography import Bibliography
from ebl.corpus.application.lines_updater import LinesUpdater
from ebl.corpus.domain.chapter import Chapter
from ebl.corpus.domain.lines_update import LinesUpdate
from ebl.corpus.infrastructure.mongo_text_repository import MongoTextRepository
from ebl.dictionary.domain.word import WordId
from ebl.tests.corpus.outline_support import (
    create_chapter_with_lines,
    create_outline_chapter,
    remove_token_fields,
)
from ebl.tests.corpus.support import (
    allow_references,
    allow_signs,
    create_chapter_dto,
    create_chapter_url,
)
from ebl.tests.factories.corpus import ChapterFactory, LineFactory
from ebl.tests.transliteration.storage_test_helpers import has_key
from ebl.transliteration.application.sign_repository import SignRepository
from ebl.transliteration.domain.line_number import LineNumber
from ebl.transliteration.domain.sign import Sign
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


def create_page(chapter: Chapter, offset: int, limit: int, tokens: bool = False) -> Dto:
    lines = create_chapter_dto(chapter)["lines"][offset:][:limit]
    return {
        "total": len(chapter.lines),
        "offset": offset,
        "limit": limit,
        "lines": lines if tokens else [remove_token_fields(line) for line in lines],
    }


def get_page(client: testing.TestClient, chapter: Chapter, query_string: str) -> Dto:
    url = create_chapter_url(chapter, "/lines")
    result = client.simulate_get(url, query_string=query_string)
    assert isinstance(result, testing.Result)
    assert result.status == falcon.HTTP_OK
    return cast(Dto, result.json)


@pytest.fixture
def chapter(text_repository: MongoTextRepository) -> Chapter:
    chapter = create_chapter_with_lines(LINE_COUNT)
    text_repository.create_chapter(chapter)
    return chapter


@pytest.mark.parametrize(
    "query_string,offset,limit,line_count,tokens",
    [
        ("", 0, 10, 10, False),
        ("tokens=false", 0, 10, 10, False),
        ("tokens=true", 0, 10, 10, True),
        ("limit=1", 0, 1, 1, False),
        ("offset=3&limit=4", 3, 4, 4, False),
        ("offset=10", 10, 10, 2, False),
        ("offset=9&limit=50&tokens=true", 9, 50, 3, True),
        ("limit=50", 0, 50, 12, False),
        ("offset=12", 12, 10, 0, False),
        ("offset=2147483647&limit=50", 2147483647, 50, 0, False),
    ],
)
def test_get_lines_page(
    client: testing.TestClient,
    chapter: Chapter,
    query_string: str,
    offset: int,
    limit: int,
    line_count: int,
    tokens: bool,
) -> None:
    page = get_page(client, chapter, query_string)

    assert page == create_page(chapter, offset, limit, tokens)
    assert len(page["lines"]) == line_count
    assert has_key(page, "reconstructionTokens") is tokens
    assert has_key(page, "atfTokens") is tokens


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

    assert first_page == create_page(chapter, 0, 2)
    assert second_page == create_page(updated_chapter, 0, 2)
    assert second_page["total"] == LINE_COUNT - 1


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


@pytest.mark.parametrize(
    "create_chapter,index,tokens",
    [
        (create_outline_chapter, 0, "false"),
        (create_outline_chapter, 1, "false"),
        (create_outline_chapter, 2, "false"),
        (create_outline_chapter, 0, "true"),
        (create_lemmatized_chapter, 1, "false"),
        (create_lemmatized_chapter, 1, "true"),
    ],
)
def test_posting_a_fetched_line_back_does_not_change_the_chapter(
    client: testing.TestClient,
    text_repository: MongoTextRepository,
    bibliography: Bibliography,
    sign_repository: SignRepository,
    signs: List[Sign],
    create_chapter: Callable[[], Chapter],
    index: int,
    tokens: str,
) -> None:
    allow_signs(signs, sign_repository)
    chapter = create_chapter()
    allow_references(chapter, bibliography)
    text_repository.create_chapter(chapter)
    updater = LinesUpdater(LinesUpdate([], set(), {}), sign_repository)
    unchanged_chapter = updater.update(chapter)
    page = get_page(client, chapter, f"offset={index}&limit=1&tokens={tokens}")
    edit = {"index": index, "line": page["lines"][0]}

    post_result = client.simulate_post(
        create_chapter_url(chapter, "/lines"),
        body=json.dumps({"new": [], "deleted": [], "edited": [edit]}),
    )

    assert isinstance(post_result, testing.Result)
    assert post_result.status == falcon.HTTP_OK
    assert post_result.json == create_chapter_dto(unchanged_chapter)
    assert text_repository.find_chapter(chapter.id_).lines == unchanged_chapter.lines
    assert get_page(client, chapter, "limit=50") == create_page(chapter, 0, 50)
