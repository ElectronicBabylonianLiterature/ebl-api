import ebl.transliteration.domain.atf as atf
from ebl.transliteration.domain.greek_tokens import GreekLetter


def test_greek_letter() -> None:
    alphabet = "a"
    flag = atf.Flag.UNCERTAIN
    greek_letter = GreekLetter.of(alphabet, [flag])

    assert greek_letter.value == f"{alphabet}{flag.value}"
    assert greek_letter.clean_value == alphabet
    assert greek_letter.get_key() == f"GreekLetter⁝{greek_letter.value}"
    assert greek_letter.lemmatizable is False
