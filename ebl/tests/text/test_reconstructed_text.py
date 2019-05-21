# type: ignore
import pytest

from ebl.text.enclosure import Enclosures
from ebl.text.reconstructed_text import AkkadianWord, Caesura, EnclosurePart, \
    Lacuna, LacunaPart, MetricalFootSeparator, Modifier, SeparatorPart, \
    StringPart


@pytest.mark.parametrize('word,expected', [
    (AkkadianWord((StringPart('ibnû'), )), 'ibnû'),
    (AkkadianWord((StringPart('ibnû'), ),
                  (Modifier.UNCERTAIN, Modifier.DAMAGED, Modifier.CORRECTED)),
     'ibnû?#!'),
    (AkkadianWord((EnclosurePart(Enclosures.BROKEN_OFF_OPEN),
                   StringPart('ibnû'))), '[ibnû'),
    (AkkadianWord((EnclosurePart(Enclosures.BROKEN_OFF_OPEN),
                   EnclosurePart(Enclosures.MAYBE_BROKEN_OFF_OPEN),
                   StringPart('ib'),
                   EnclosurePart(Enclosures.MAYBE_BROKEN_OFF_CLOSE),
                   StringPart('nû'),
                   EnclosurePart(Enclosures.BROKEN_OFF_CLOSE))),
     '[(ib)nû]'),
    (AkkadianWord((StringPart('ibnû'),
                   EnclosurePart(Enclosures.MAYBE_BROKEN_OFF_CLOSE),
                   EnclosurePart(Enclosures.BROKEN_OFF_CLOSE),),
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
    (Lacuna((Enclosures.BROKEN_OFF_OPEN, ), tuple()), '[...'),
    (Lacuna(tuple(), (Enclosures.MAYBE_BROKEN_OFF_CLOSE, )), '...)'),
    (Lacuna((Enclosures.BROKEN_OFF_OPEN, Enclosures.MAYBE_BROKEN_OFF_OPEN),
            (Enclosures.MAYBE_BROKEN_OFF_CLOSE, )), '[(...)')
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
