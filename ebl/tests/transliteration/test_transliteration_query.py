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
    ("|U.BA|", True),
    ("|U.BA| BA", False),
    ("BA ? TA", True),
    ("MU ? TA", False),
    ("KI * TA", True),
    ("KI * DU", False),
    ("[UD|TA|NU] MA", True),
    ("[UD|BA] NU", False),
    ("[UD|TA|NU] MA\nKI", True),
    ("[UD|TA|NU] MA\nKI * BA", True),
    ("[UD|TA|NU] MA\nKI * NU", False),
]


@pytest.mark.parametrize("string,is_match", REGEXP_DATA)
def test_regexp(string, is_match, sign_repository, signs):
    for sign in signs:
        sign_repository.create(sign)
    query = TransliterationQuery(string=string, sign_repository=sign_repository)
    match = re.search(
        query.regexp,
        "KU NU IGI\n"
        "MI DIŠ MI UD MA\n"
        "KI DU ABZ411 BA MA TA\n"
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
    ("\nAŠ", False),
]


@pytest.mark.parametrize("string, expected", GET_IS_SEQUENCE_EMPTY_DATA)
def test_is_sequence_empty(string, expected, sign_repository):
    query = TransliterationQuery(string=string, sign_repository=sign_repository)
    assert expected == query.is_empty()
