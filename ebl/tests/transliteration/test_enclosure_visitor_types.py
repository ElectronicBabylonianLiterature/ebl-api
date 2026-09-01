from typing import Sequence
from ebl.tests.transliteration.enclosure_visitor_types_cases_1 import (
    ENCLOSURE_VISITOR_TYPES_CASES_1,
)
from ebl.tests.transliteration.enclosure_visitor_types_cases_2 import (
    ENCLOSURE_VISITOR_TYPES_CASES_2,
)

import pytest

from ebl.transliteration.domain.enclosure_visitor import EnclosureUpdater
from ebl.transliteration.domain.atf_parsers.lark_parser import parse_line
from ebl.transliteration.domain.tokens import (
    Token,
)


def map_line(atf) -> Sequence[Token]:
    visitor = EnclosureUpdater()
    parse_line(f"1. {atf}").accept(visitor)
    return visitor.tokens


@pytest.mark.parametrize(
    "atf, expected",
    [
        *ENCLOSURE_VISITOR_TYPES_CASES_1,
        *ENCLOSURE_VISITOR_TYPES_CASES_2,
    ],
)
def test_enclosure_type(atf, expected):
    assert map_line(atf) == expected
