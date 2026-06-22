import pytest
from lark.exceptions import UnexpectedCharacters, VisitError

from ebl.transliteration.domain.atf_parsers.lark_parser_errors import (
    create_transliteration_error_data,
)
from ebl.transliteration.domain.transliteration_error import ErrorAnnotation


def test_unexpected_input_is_annotated() -> None:
    line = "1. foobar baz"
    error = UnexpectedCharacters(line, 3, 1, 4)

    annotation = create_transliteration_error_data(error, line, 0)

    assert isinstance(annotation, ErrorAnnotation)
    assert annotation.description.startswith("Invalid line: ")
    assert "^" in annotation.description
    assert annotation.line_number == 1


def test_visit_error_without_duplicate_status_is_reraised() -> None:
    error = VisitError("rule", "tree", ValueError("boom"))

    with pytest.raises(VisitError):
        create_transliteration_error_data(error, "1. line", 0)


def test_unregistered_error_is_reraised() -> None:
    error = KeyError("unexpected")

    with pytest.raises(KeyError):
        create_transliteration_error_data(error, "1. line", 0)
