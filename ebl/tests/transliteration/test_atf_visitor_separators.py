from ebl.transliteration.domain import atf
from ebl.transliteration.domain.atf_visitor import convert_to_atf
from ebl.transliteration.domain.egyptian_metrical_feet_separator_token import (
    EgyptianMetricalFeetSeparator,
)
from ebl.transliteration.domain.enclosure_tokens import Removal
from ebl.transliteration.domain.sign_tokens import Reading
from ebl.transliteration.domain.word_tokens import Word


def test_a_removal_wraps_the_words_it_encloses() -> None:
    tokens = [
        Removal.open(),
        Word.of([Reading.of_name("ku")]),
        Removal.close(),
    ]

    assert convert_to_atf(None, tokens) == "<<ku>>"


def test_a_removal_keeps_the_separator_before_it() -> None:
    tokens = [
        Word.of([Reading.of_name("nu")]),
        Removal.open(),
        Word.of([Reading.of_name("ku")]),
        Removal.close(),
    ]

    assert convert_to_atf(None, tokens) == "nu <<ku>>"


def test_an_egyptian_metrical_feet_separator_is_forced_apart() -> None:
    tokens = [
        Word.of([Reading.of_name("ku")]),
        EgyptianMetricalFeetSeparator.of(),
        Word.of([Reading.of_name("nu")]),
    ]

    separator = atf.EGYPTIAN_METRICAL_FEET_SEPARATOR

    assert convert_to_atf(None, tokens) == f"ku {separator} nu"


def test_a_flagged_egyptian_metrical_feet_separator_keeps_its_flags() -> None:
    token = EgyptianMetricalFeetSeparator.of([atf.Flag.DAMAGE])

    assert convert_to_atf(None, [token]) == token.value
    assert token.clean_value == atf.EGYPTIAN_METRICAL_FEET_SEPARATOR
