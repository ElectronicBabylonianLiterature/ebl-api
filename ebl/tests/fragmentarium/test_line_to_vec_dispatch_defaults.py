import pytest

from ebl.fragmentarium.application.matches.create_line_to_vec import (
    get_line_number,
    get_line_number_prefix_modifier,
    get_line_number_prime,
    parse_text_line,
)
from ebl.transliteration.domain.line_number import AbstractLineNumber


class _UnregisteredLineNumber(AbstractLineNumber):
    @property
    def atf(self) -> str:
        return "?"

    @property
    def label(self) -> str:
        return "?"

    @property
    def is_beginning_of_side(self) -> bool:
        return False

    @property
    def is_end_of_side(self) -> bool:
        return False

    def is_matching_number(self, number: int) -> bool:
        return False


@pytest.mark.parametrize(
    "overload",
    [
        get_line_number_prime,
        get_line_number_prefix_modifier,
        parse_text_line,
        get_line_number,
    ],
)
def test_an_unregistered_line_number_has_no_default_overload(overload) -> None:
    with pytest.raises(ValueError, match="No default for overloading"):
        overload(_UnregisteredLineNumber())
