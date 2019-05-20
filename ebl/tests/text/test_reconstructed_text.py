import pytest

from ebl.text.reconstructed_text import AkkadianWord, Modifier, \
    BrokenOffOpen, BrokenOffClose, StringPart, BrokenOffPart, Lacuna, \
    Caesura, MetricalFootSeparator, LacunaPart, SeparatorPart


@pytest.mark.parametrize('word,expected', [
    (AkkadianWord((StringPart('ibnû'), )), 'ibnû'),
    (AkkadianWord((StringPart('ibnû'), ),
                  (Modifier.UNCERTAIN, Modifier.BROKEN, Modifier.CORRECTED)),
     'ibnû?#!'),
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
                  (Modifier.UNCERTAIN, )), 'ibnû?)]'),
    (AkkadianWord((StringPart('ib'), LacunaPart(), StringPart('nû'))),
     'ib...nû'),
    (AkkadianWord((StringPart('ib'), SeparatorPart(), StringPart('nû'))),
     'ib-nû')
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


@pytest.mark.parametrize('caesura,expected', [
    (Caesura(False), '||'),
    (Caesura(True), '(||)')
])
def test_caesura(caesura, expected):
    assert str(caesura) == expected


@pytest.mark.parametrize('separator,expected', [
    (MetricalFootSeparator(False), '|'),
    (MetricalFootSeparator(True), '(|)')
])
def test_metrical_foot_separator(separator, expected):
    assert str(separator) == expected
