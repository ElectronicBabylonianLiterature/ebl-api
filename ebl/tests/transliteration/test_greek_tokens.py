from ebl.tests.asserts import assert_token_serialization

import ebl.transliteration.domain.atf as atf
from ebl.transliteration.domain.greek_tokens import GreekLetter


def test_greek_letter() -> None:
    alphabet = "α"
    flag = atf.Flag.UNCERTAIN
    greek_letter = GreekLetter.of(alphabet, [flag])

    assert greek_letter.value == f"{alphabet}{flag.value}"
    assert greek_letter.clean_value == alphabet
    assert greek_letter.get_key() == f"GreekLetter⁝{greek_letter.value}"
    assert greek_letter.lemmatizable is False

    serialized = {"type": "GreekLetter", "letter": alphabet, "flags": [flag.value]}
    assert_token_serialization(greek_letter, serialized)
