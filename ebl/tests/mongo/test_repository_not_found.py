import pytest

from ebl.errors import NotFoundError
from ebl.transliteration.domain.sign_tokens import SignName

MISSING_IDENTIFIER = "missing-identifier"


def assert_message(excinfo, expected: str) -> None:
    message = str(excinfo.value)
    assert message == expected
    assert "{" not in message
    assert "$" not in message
    assert "_id" not in message


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
