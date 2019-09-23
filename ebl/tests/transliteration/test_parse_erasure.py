import pytest

from ebl.transliteration.lark_parser import parse_erasure
from ebl.transliteration.text_parser import erasure
from ebl.transliteration.token import Erasure, ErasureState, Side, Word

ERASURE_LEFT = Erasure('°', Side.LEFT)
ERASURE_CENTER = Erasure('\\', Side.CENTER)
ERASURE_RIGHT = Erasure('°', Side.RIGHT)


@pytest.mark.parametrize('parser', [
    parse_erasure,
    erasure(True).parse
])
@pytest.mark.parametrize('atf,erased,over_erased', [
    ('°ku\\ku°', [Word('ku', erasure=ErasureState.ERASED)],
     [Word('ku', erasure=ErasureState.OVER_ERASED)]),
    ('°\\ku°', [], [Word('ku', erasure=ErasureState.OVER_ERASED)]),
    ('°ku\\°', [Word('ku', erasure=ErasureState.ERASED)], []),
    ('°\\°', [], []),
    ('°x X\\X x°',
     [Word('x', erasure=ErasureState.ERASED),
      Word('X', erasure=ErasureState.ERASED)],
     [Word('X', erasure=ErasureState.OVER_ERASED),
      Word('x', erasure=ErasureState.OVER_ERASED)])
])
def test_erasure(parser, atf, erased, over_erased):
    assert parser(atf) == [ERASURE_LEFT, erased, ERASURE_CENTER,
                           over_erased, ERASURE_RIGHT]
