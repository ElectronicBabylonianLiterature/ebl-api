import pytest

from ebl.text.reconstructed_text import AkkadianWord, Modifier, \
    BrokenOffOpen, BrokenOffClose, StringPart, BrokenOffPart, Lacuna


@pytest.mark.parametrize('word,expected', [
    (AkkadianWord((StringPart('ibnû'), )), 'ibnû'),
    (AkkadianWord((StringPart('ibnû'), ),
                  (Modifier.UNCERTAIN, Modifier.BROKEN)), 'ibnû?#'),
    (AkkadianWord((BrokenOffPart(BrokenOffOpen.BROKEN),
                   StringPart('ibnû'))), '[ibnû'),
    (AkkadianWord((BrokenOffPart(BrokenOffOpen.BOTH),
                   StringPart('ib'),
                   BrokenOffPart(BrokenOffClose.MAYBE),
                   StringPart('nû'),
                   BrokenOffPart(BrokenOffClose.BROKEN))),
     '[(ib)nû]'),
    (AkkadianWord((StringPart('ibnû'),
                   BrokenOffPart(BrokenOffClose.BOTH)),
                  (Modifier.UNCERTAIN, )), 'ibnû?)]')
])
def test_akkadian_word(word, expected):
    assert str(word) == expected


@pytest.mark.parametrize('lacuna,expected', [
    (Lacuna((None, None)), '...'),
    (Lacuna((BrokenOffOpen.BROKEN, None)), '[...'),
    (Lacuna((None, BrokenOffClose.MAYBE)), '...)'),
    (Lacuna((BrokenOffOpen.BOTH, BrokenOffClose.MAYBE)), '[(...)')
])
def test_lacuna(lacuna, expected):
    assert str(lacuna) == expected
