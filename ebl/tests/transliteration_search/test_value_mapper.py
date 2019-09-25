from typing import Any

import pytest

from ebl.transliteration_search.domain.sign import SignName
from ebl.transliteration_search.domain.value import Grapheme, \
    INVALID_READING, \
    NotReading, \
    Reading, \
    SplittableGrapheme, Variant
from ebl.transliteration_search.domain.value_mapper import parse_reading


@pytest.mark.parametrize('value,expected', [
    ('nu', Reading('nu', 1, INVALID_READING)),
    ('šu', Reading('šu', 1, INVALID_READING)),
    ('gid₂', Reading('gid', 2, INVALID_READING)),
    ('|BIxIS|', Grapheme(SignName('|BIxIS|'))),
    ('|BI×IS|', Grapheme(SignName('|BI×IS|'))),
    ('|BI.IS|', SplittableGrapheme.of([SignName('BI'), SignName('IS')])),
    ('|BI.IS+IS|', SplittableGrapheme.of([SignName('BI'), SignName('IS+IS')])),
    ('|BI.(IS+IS)|',  Grapheme(SignName('|BI.(IS+IS)|'))),
    ('|BI+IS|', Grapheme(SignName('|BI+IS|'))),
    ('|BI&IS|', Grapheme(SignName('|BI&IS|'))),
    ('|BI%IS|', Grapheme(SignName('|BI%IS|'))),
    ('|BI@IS|', Grapheme(SignName('|BI@IS|'))),
    ('|3×BI|', Grapheme(SignName('|3×BI|'))),
    ('|3xBI|', Grapheme(SignName('|3xBI|'))),
    ('|GEŠTU~axŠE~a@t|', Grapheme(SignName('|GEŠTU~axŠE~a@t|'))),
    ('|(GI&GI)×ŠE₃|', Grapheme(SignName('|(GI&GI)×ŠE₃|'))),
    ('unknown', Reading('unknown', 1, INVALID_READING)),
    ('nuₓ', NotReading('?')),
    ('x', NotReading('X')),
    ('X', NotReading('X')),
    ('1(AŠ)', Grapheme(SignName('AŠ'))),
    # 1, 2, 5, 10, 20, 30 should be inserted manually to the sign list
    ('1', Reading('1', 1, '1')),
    ('foo(TUKUL)', Grapheme(SignName('TUKUL'))),
    ('foo(|BI×IS|)', Grapheme(SignName('|BI×IS|'))),
    ('foo(|BI.IS|)',  SplittableGrapheme.of([SignName('BI'),
                                             SignName('IS')])),
    ('šu/gid₂', Variant((
        Reading('šu', 1, INVALID_READING),
        Reading('gid', 2, INVALID_READING)
    ))),
    ('šu/gid₂/nu', Variant((
        Reading('šu', 1, INVALID_READING),
        Reading('gid', 2, INVALID_READING),
        Reading('nu', 1, INVALID_READING)
    ))),
    ('šu/|BI.IS|', Variant((
        Reading('šu', 1, INVALID_READING),
        Grapheme(SignName('|BI.IS|'))
    ))),
    ('šu/|BI×IS|', Variant((
        Reading('šu', 1, INVALID_READING),
        Grapheme(SignName('|BI×IS|'))
    ))),
    ('|BI×IS|/šu', Variant((
        Grapheme(SignName('|BI×IS|')),
        Reading('šu', 1, INVALID_READING)
    ))),
    ('šu/|BI×IS|/nu', Variant((
        Reading('šu', 1, INVALID_READING),
        Grapheme(SignName('|BI×IS|')),
        Reading('nu', 1, INVALID_READING)
    ))),
    ('foo(TUKUL)/šu', Variant((
        Grapheme(SignName('TUKUL')),
        Reading('šu', 1, INVALID_READING)
    ))),
    ('foo(|BI×IS|)/šu', Variant((
        Grapheme(SignName('|BI×IS|')),
        Reading('šu', 1, INVALID_READING)
    ))),
    ('šu/1(AŠ)', Variant((
        Reading('šu', 1, INVALID_READING),
        Grapheme(SignName('AŠ'))
    ))),
    ('256/nu', Variant((
        Reading('256', 1, '256'),
        Reading('nu', 1, INVALID_READING)
    ))),
    ('x/nu', Variant((NotReading('X'), Reading('nu', 1, INVALID_READING)))),
    ('nu/unknown', Variant((
        Reading('nu', 1, INVALID_READING),
        Reading('unknown', 1, INVALID_READING)
    ))),
    ('unknown/x', Variant((
        Reading('unknown', 1, INVALID_READING),
        NotReading('X')
    ))),
    ('', NotReading(''))
])
def test_parse_reading(value, expected):
    assert parse_reading(value) == expected


def test_nested_variants_are_invalid():
    with pytest.raises(ValueError):
        Variant((
            Variant((
                Reading('kur', 1, INVALID_READING),
                NotReading('X'),
            )),
            NotReading('X')
        ))


def test_variant_cannot_contain_splittable_grapheme():
    with pytest.raises(ValueError):
        Variant((
            SplittableGrapheme((
                Grapheme(SignName('BI')),
                Grapheme(SignName('BI'))
            )),
            NotReading('X')
        ))


@pytest.mark.parametrize('value', [
    Reading('šu', 1, INVALID_READING),
    NotReading('X'),
    Variant((
        Reading('kur', 1, INVALID_READING),
        NotReading('X')
    )),
    SplittableGrapheme((
        Grapheme(SignName('BI')),
        Grapheme(SignName('BI'))
    ))
])
def test_splittable_grapheme_can_only_contain_graphemes(value):
    fake_grapheme: Any = value
    with pytest.raises(ValueError):
        SplittableGrapheme((fake_grapheme, Grapheme(SignName('BI'))))
