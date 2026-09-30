import pytest

from ebl.common.domain.stage import Stage
from ebl.corpus.domain.chapter import ChapterId
from ebl.errors import NotFoundError
from ebl.tests.factories.corpus import ChapterFactory
from ebl.tests.mongo.sanitization_helpers import assert_no_query_details
from ebl.transliteration.domain.genre import Genre
from ebl.transliteration.domain.sign_tokens import SignName
from ebl.transliteration.domain.text_id import TextId

MISSING_IDENTIFIER = "missing-identifier"
MISSING_CHAPTER_ID = ChapterId(
    TextId(Genre.LITERATURE, 1, 99), Stage.OLD_BABYLONIAN, "missing"
)


def assert_message(excinfo, expected: str) -> None:
    message = str(excinfo.value)
    assert message == expected
    assert_no_query_details(message)


def test_word_repository_reports_identifier(word_repository) -> None:
    with pytest.raises(NotFoundError) as excinfo:
        word_repository.query_by_id(MISSING_IDENTIFIER)

    assert_message(excinfo, f"word {MISSING_IDENTIFIER} not found.")


def test_sign_repository_reports_identifier(sign_repository) -> None:
    with pytest.raises(NotFoundError) as excinfo:
        sign_repository.find(SignName(MISSING_IDENTIFIER))

    assert_message(excinfo, f"sign {MISSING_IDENTIFIER} not found.")


def test_bibliography_repository_reports_identifier(bibliography_repository) -> None:
    with pytest.raises(NotFoundError) as excinfo:
        bibliography_repository.query_by_id(MISSING_IDENTIFIER)

    assert_message(excinfo, f"bibliography {MISSING_IDENTIFIER} not found.")


def test_provenance_repository_reports_identifier(provenance_repository) -> None:
    with pytest.raises(NotFoundError) as excinfo:
        provenance_repository.query_by_id(MISSING_IDENTIFIER)

    assert_message(excinfo, f"provenance {MISSING_IDENTIFIER} not found.")


def test_provenance_repository_hides_query(provenance_repository) -> None:
    with pytest.raises(NotFoundError) as excinfo:
        provenance_repository.query_by_long_name(MISSING_IDENTIFIER)

    assert_message(excinfo, "provenance not found.")


def test_cache_repository_hides_query(mongo_cache_repository) -> None:
    with pytest.raises(NotFoundError) as excinfo:
        mongo_cache_repository.get(MISSING_IDENTIFIER)

    assert_message(excinfo, "cache not found.")


def test_word_repository_update_reports_identifier(word_repository) -> None:
    with pytest.raises(NotFoundError) as excinfo:
        word_repository.update({"_id": MISSING_IDENTIFIER, "lemma": ["missing"]})

    assert_message(excinfo, f"word {MISSING_IDENTIFIER} not found.")


def test_corpus_chapter_update_hides_query(text_repository) -> None:
    with pytest.raises(NotFoundError) as excinfo:
        text_repository.update(MISSING_CHAPTER_ID, ChapterFactory.build())

    assert_message(excinfo, "chapter not found.")
