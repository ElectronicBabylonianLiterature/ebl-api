import pytest

from ebl.corpus.domain.chapter import ChapterId
from ebl.common.query.query_result import CorpusQueryResult
from ebl.errors import NotFoundError
from ebl.transliteration.domain.genre import Genre
from ebl.common.domain.stage import Stage
from ebl.transliteration.domain.text_id import TextId

MISSING_CHAPTER = ChapterId(TextId(Genre.LITERATURE, 9, 99), Stage.OLD_BABYLONIAN, "?")


def _line_dto(genre: Genre, index: int) -> dict:
    return {"textId": {"genre": genre.value}, "index": index}


def test_the_genre_limit_keeps_at_most_ten_lines_per_genre(text_repository) -> None:
    cursor = [_line_dto(Genre.LITERATURE, index) for index in range(25)]

    limited = text_repository._limit_by_genre(cursor)

    assert len(limited) == 10


def test_the_genre_limit_stops_once_forty_lines_are_collected(text_repository) -> None:
    genres = [Genre.LITERATURE, Genre.DIVINATION, Genre.LEXICOGRAPHY, Genre.MAGIC]
    cursor = [_line_dto(genre, index) for genre in genres for index in range(10)] + [
        _line_dto(Genre.MEDICINE, index) for index in range(10)
    ]

    limited = text_repository._limit_by_genre(cursor)

    assert len(limited) == 40
    assert {line["textId"]["genre"] for line in limited} == {
        genre.value for genre in genres
    }


def test_the_genre_limit_returns_everything_below_the_cap(text_repository) -> None:
    cursor = [_line_dto(Genre.LITERATURE, index) for index in range(3)]

    assert text_repository._limit_by_genre(cursor) == cursor


def test_a_query_with_only_a_lemma_operator_returns_an_empty_result(
    text_repository,
) -> None:
    assert text_repository.query({"lemmaOperator": "and"}) == (
        CorpusQueryResult.create_empty()
    )


def test_an_entirely_empty_query_returns_an_empty_result(text_repository) -> None:
    assert text_repository.query({}) == CorpusQueryResult.create_empty()


def test_querying_manuscripts_with_joins_on_a_missing_chapter_is_empty(
    text_repository,
) -> None:
    assert (
        text_repository.query_manuscripts_with_joins_by_chapter(MISSING_CHAPTER) == []
    )


def test_querying_manuscripts_on_a_missing_chapter_is_not_found(
    text_repository,
) -> None:
    with pytest.raises(NotFoundError):
        text_repository.query_manuscripts_by_chapter(MISSING_CHAPTER)
