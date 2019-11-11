import pytest

from ebl.transliteration.domain.lark_parser import parse_erasure
from ebl.transliteration.domain.token import Erasure, ErasureState, Side, \
    Word, ValueToken

ERASURE_LEFT = Erasure('°', Side.LEFT)
ERASURE_CENTER = Erasure('\\', Side.CENTER)
ERASURE_RIGHT = Erasure('°', Side.RIGHT)


@pytest.mark.parametrize('parser', [
    parse_erasure
])
@pytest.mark.parametrize('atf,erased,over_erased', [
    ('°ku\\ku°', [Word('ku', erasure=ErasureState.ERASED, parts=[
        ValueToken('ku')
    ])],
     [Word('ku', erasure=ErasureState.OVER_ERASED, parts=[
        ValueToken('ku')
     ])]),
    ('°\\ku°', [], [Word('ku', erasure=ErasureState.OVER_ERASED, parts=[
        ValueToken('ku')
    ])]),
    ('°ku\\°', [Word('ku', erasure=ErasureState.ERASED, parts=[
        ValueToken('ku')
    ])], []),
    ('°\\°', [], []),
    ('°x X\\X x°',
     [Word('x', erasure=ErasureState.ERASED, parts=[
        ValueToken('x')
      ]),
      Word('X', erasure=ErasureState.ERASED, parts=[
        ValueToken('X')
      ])],
     [Word('X', erasure=ErasureState.OVER_ERASED, parts=[
        ValueToken('X')
     ]),
      Word('x', erasure=ErasureState.OVER_ERASED, parts=[
        ValueToken('x')
      ])])
])
def test_erasure(parser, atf, erased, over_erased):
    assert parser(atf) == [ERASURE_LEFT, erased, ERASURE_CENTER,
                           over_erased, ERASURE_RIGHT]
