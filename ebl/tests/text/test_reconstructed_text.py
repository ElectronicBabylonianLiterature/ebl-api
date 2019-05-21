import pytest

from ebl.text.reconstructed_text import AkkadianWord, Caesura, Enclosure, \
    EnclosurePart, Lacuna, LacunaPart, MetricalFootSeparator, Modifier, \
    SeparatorPart, StringPart


@pytest.mark.parametrize('word,expected', [
    (AkkadianWord((StringPart('ibnû'), )), 'ibnû'),
    (AkkadianWord((StringPart('ibnû'), ),
                  (Modifier.UNCERTAIN, Modifier.BROKEN, Modifier.CORRECTED)),
     'ibnû?#!'),
    (AkkadianWord((EnclosurePart(Enclosure.BROKEN_OFF_OPEN),
                   StringPart('ibnû'))), '[ibnû'),
    (AkkadianWord((EnclosurePart(Enclosure.BROKEN_OFF_OPEN),
                   EnclosurePart(Enclosure.MAYBE_BROKEN_OFF_OPEN),
                   StringPart('ib'),
                   EnclosurePart(Enclosure.MAYBE_BROKEN_OFF_CLOSE),
                   StringPart('nû'),
                   EnclosurePart(Enclosure.BROKEN_OFF_CLOSE))),
     '[(ib)nû]'),
    (AkkadianWord((StringPart('ibnû'),
                   EnclosurePart(Enclosure.MAYBE_BROKEN_OFF_CLOSE),
                   EnclosurePart(Enclosure.BROKEN_OFF_CLOSE),),
                  (Modifier.UNCERTAIN, )), 'ibnû?)]'),
    (AkkadianWord((StringPart('ib'), LacunaPart(), StringPart('nû'))),
     'ib...nû'),
    (AkkadianWord((StringPart('ib'), SeparatorPart(), StringPart('nû'))),
     'ib-nû')
])
def test_akkadian_word(word, expected):
    assert str(word) == expected


@pytest.mark.parametrize('lacuna,expected', [
    (Lacuna(tuple(), tuple()), '...'),
    (Lacuna((Enclosure.BROKEN_OFF_OPEN, ), tuple()), '[...'),
    (Lacuna(tuple(), (Enclosure.MAYBE_BROKEN_OFF_CLOSE, )), '...)'),
    (Lacuna((Enclosure.BROKEN_OFF_OPEN, Enclosure.MAYBE_BROKEN_OFF_OPEN),
            (Enclosure.MAYBE_BROKEN_OFF_CLOSE, )), '[(...)')
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
