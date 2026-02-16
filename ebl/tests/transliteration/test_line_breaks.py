from ebl.tests.asserts import assert_token_serialization
from ebl.transliteration.domain.enclosure_type import EnclosureType
from ebl.transliteration.domain.tokens import ErasureState, LineBreak
from ebl.transliteration.domain.word_tokens import InWordNewline


def test_in_word_new_line():
    newline = InWordNewline(frozenset({EnclosureType.BROKEN_AWAY}), ErasureState.NONE)

    expected_value = ";"
    assert newline.value == expected_value
    assert newline.clean_value == expected_value
    assert newline.get_key() == f"InWordNewline⁝{expected_value}"
    assert newline.lemmatizable is False

    serialized = {"type": "InWordNewline"}
    assert_token_serialization(newline, serialized)


def test_line_break():
    value = "|"
    line_break = LineBreak.of()

    assert line_break.value == value
    assert line_break.clean_value == value
    assert line_break.get_key() == f"LineBreak⁝{value}"
    assert line_break.lemmatizable is False

    serialized = {"type": "LineBreak"}
    assert_token_serialization(line_break, serialized)
