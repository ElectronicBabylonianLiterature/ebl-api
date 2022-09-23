import re

import pytest

from ebl.transliteration.domain.transliteration_query import TransliterationQuery

REGEXP_DATA = [
    ("DU U", True),
    ("KU", True),
    ("UD", True),
    ("GI₆ DIŠ\nU BA MA", True),
    ("ŠU", True),
    ("IGI UD", False),
    ("|U.BA|", False),
]


@pytest.mark.parametrize("signs,is_match", REGEXP_DATA)
def test_regexp(signs, is_match, sign_repository):
    query = TransliterationQuery(
        string=signs, sign_repository=sign_repository)
    match = re.search(
        query.regexp,
        "KU NU IGI\n"
        "GI₆ DIŠ GI₆ UD MA\n"
        "KI DU U BA MA TA\n"
        "X MU TA MA UD\n"
        "ŠU/BU",
    )

    if is_match:
        assert match is not None
    else:
        assert match is None


GET_IS_SEQUENCE_EMPTY_DATA = [
    ("", True),
    ("MA TA", False),
    ("\n", True),
    ("\nABZ001", False),
]


@pytest.mark.parametrize("query, expected", GET_IS_SEQUENCE_EMPTY_DATA)
def test_is_sequence_empty(query, expected, sign_repository):
    query = TransliterationQuery(string=query, sign_repository=sign_repository)
    assert expected == query.is_empty()
