import pytest

from ebl.text.reconstructed_text import AkkadianWord, Modifier, \
    BrokenOffOpen, BrokenOffClose, StringPart, BrokenOffPart


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
