import pytest

from ebl.text.enclosure import BROKEN_OFF_OPEN, BROKEN_OFF_CLOSE, \
    MAYBE_BROKEN_OFF_OPEN, MAYBE_BROKEN_OFF_CLOSE, EMENDATION_OPEN, \
    EMENDATION_CLOSE
from ebl.text.reconstructed_text import AkkadianWord, Caesura, EnclosurePart, \
    Lacuna, LacunaPart, MetricalFootSeparator, Modifier, SeparatorPart, \
    StringPart


@pytest.mark.parametrize('word,expected', [
    (AkkadianWord((StringPart('ibnû'), )), 'ibnû'),
    (AkkadianWord((StringPart('ibnû'), ),
                  (Modifier.UNCERTAIN, Modifier.DAMAGED, Modifier.CORRECTED)),
     'ibnû?#!'),
    (AkkadianWord((EnclosurePart(BROKEN_OFF_OPEN),
                   StringPart('ibnû'))), '[ibnû'),
    (AkkadianWord((EnclosurePart(BROKEN_OFF_OPEN),
                   EnclosurePart(MAYBE_BROKEN_OFF_OPEN),
                   StringPart('ib'),
                   EnclosurePart(MAYBE_BROKEN_OFF_CLOSE),
                   StringPart('nû'),
                   EnclosurePart(BROKEN_OFF_CLOSE))),
     '[(ib)nû]'),
    (AkkadianWord((EnclosurePart(BROKEN_OFF_OPEN),
                   EnclosurePart(MAYBE_BROKEN_OFF_OPEN),
                   EnclosurePart(EMENDATION_OPEN),
                   StringPart('ib'),
                   EnclosurePart(MAYBE_BROKEN_OFF_CLOSE),
                   StringPart('nû'),
                   EnclosurePart(EMENDATION_CLOSE),
                   EnclosurePart(BROKEN_OFF_CLOSE))),
     '[(<ib)nû>]'),
    (AkkadianWord((StringPart('ibnû'),
                   EnclosurePart(MAYBE_BROKEN_OFF_CLOSE),
                   EnclosurePart(BROKEN_OFF_CLOSE),),
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
    (Lacuna((BROKEN_OFF_OPEN, ), tuple()), '[...'),
    (Lacuna(tuple(), (MAYBE_BROKEN_OFF_CLOSE, )), '...)'),
    (Lacuna((BROKEN_OFF_OPEN, MAYBE_BROKEN_OFF_OPEN),
            (MAYBE_BROKEN_OFF_CLOSE, )), '[(...)')
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
