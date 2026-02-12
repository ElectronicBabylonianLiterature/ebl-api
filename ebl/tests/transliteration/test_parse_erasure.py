import pytest

from ebl.transliteration.domain.enclosure_tokens import Erasure
from ebl.transliteration.domain.atf_parsers.lark_parser import parse_erasure
from ebl.transliteration.domain.sign_tokens import Divider, Reading
from ebl.transliteration.domain.unknown_sign_tokens import UnclearSign, UnidentifiedSign
from ebl.transliteration.domain.word_tokens import ErasureState, Word

ERASURE_LEFT = Erasure.open()
ERASURE_CENTER = Erasure.center()
ERASURE_RIGHT = Erasure.close()


@pytest.mark.parametrize("parser", [parse_erasure])
@pytest.mark.parametrize(
    "atf,erased,over_erased",
    [
        (
            "°ku\\ku°",
            (Word.of(erasure=ErasureState.ERASED, parts=[Reading.of_name("ku")]),),
            (Word.of(erasure=ErasureState.OVER_ERASED, parts=[Reading.of_name("ku")]),),
        ),
        (
            "°::\\:.°",
            (Divider.of("::").set_erasure(ErasureState.ERASED),),
            (Divider.of(":.").set_erasure(ErasureState.OVER_ERASED),),
        ),
        (
            "°\\ku°",
            (),
            (Word.of(erasure=ErasureState.OVER_ERASED, parts=[Reading.of_name("ku")]),),
        ),
        (
            "°ku\\°",
            (Word.of(erasure=ErasureState.ERASED, parts=[Reading.of_name("ku")]),),
            (),
        ),
        ("°\\°", (), ()),
        (
            "°x X\\X x°",
            (
                Word.of([UnclearSign.of()], erasure=ErasureState.ERASED),
                Word.of([UnidentifiedSign.of()], erasure=ErasureState.ERASED),
            ),
            (
                Word.of([UnidentifiedSign.of()], erasure=ErasureState.OVER_ERASED),
                Word.of([UnclearSign.of()], erasure=ErasureState.OVER_ERASED),
            ),
        ),
    ],
)
def test_erasure(parser, atf, erased, over_erased):
    assert parser(atf) == [
        ERASURE_LEFT,
        *erased,
        ERASURE_CENTER,
        *over_erased,
        ERASURE_RIGHT,
    ]
