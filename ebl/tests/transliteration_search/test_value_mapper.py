import pytest

from ebl.transliteration_search.value import Grapheme, INVALID_READING, \
    NotReading, \
    Reading, \
    SplittableGrapheme, Variant
from ebl.transliteration_search.value_mapper import parse_reading


@pytest.mark.parametrize('value,expected', [
    ('nu', Reading('nu', 1, INVALID_READING)),
    ('šu', Reading('šu', 1, INVALID_READING)),
    ('gid₂', Reading('gid', 2, INVALID_READING)),
    ('|BIxIS|', Grapheme('|BIxIS|')),
    ('|BI×IS|', Grapheme('|BI×IS|')),
    ('|BI.IS|', SplittableGrapheme((Grapheme('BI'), Grapheme('IS')))),
    ('|BI.IS+IS|', SplittableGrapheme((Grapheme('BI'), Grapheme('IS+IS')))),
    ('|BI.(IS+IS)|',  Grapheme('|BI.(IS+IS)|')),
    ('|BI+IS|', Grapheme('|BI+IS|')),
    ('|BI&IS|', Grapheme('|BI&IS|')),
    ('|BI%IS|', Grapheme('|BI%IS|')),
    ('|BI@IS|', Grapheme('|BI@IS|')),
    ('|3×BI|', Grapheme('|3×BI|')),
    ('|3xBI|', Grapheme('|3xBI|')),
    ('|GEŠTU~axŠE~a@t|', Grapheme('|GEŠTU~axŠE~a@t|')),
    ('|(GI&GI)×ŠE₃|', Grapheme('|(GI&GI)×ŠE₃|')),
    ('unknown', Reading('unknown', 1, INVALID_READING)),
    ('nuₓ', NotReading('?')),
    ('x', NotReading('X')),
    ('X', NotReading('X')),
    ('1(AŠ)', Grapheme('AŠ')),
    # 1, 2, 5, 10, 20, 30 should be inserted manually to the sign list
    ('1', Reading('1', 1, '1')),
    ('foo(TUKUL)', Grapheme('TUKUL')),
    ('foo(|BI×IS|)', Grapheme('|BI×IS|')),
    ('foo(|BI.IS|)',  SplittableGrapheme((Grapheme('BI'), Grapheme('IS')))),
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
        Grapheme('|BI.IS|')
    ))),
    ('šu/|BI×IS|', Variant((
        Reading('šu', 1, INVALID_READING),
        Grapheme('|BI×IS|')
    ))),
    ('|BI×IS|/šu', Variant((
        Grapheme('|BI×IS|'),
        Reading('šu', 1, INVALID_READING)
    ))),
    ('šu/|BI×IS|/nu', Variant((
        Reading('šu', 1, INVALID_READING),
        Grapheme('|BI×IS|'),
        Reading('nu', 1, INVALID_READING)
    ))),
    ('foo(TUKUL)/šu', Variant((
        Grapheme('TUKUL'),
        Reading('šu', 1, INVALID_READING)
    ))),
    ('foo(|BI×IS|)/šu', Variant((
        Grapheme('|BI×IS|'),
        Reading('šu', 1, INVALID_READING)
    ))),
    ('šu/1(AŠ)', Variant((
        Reading('šu', 1, INVALID_READING),
        Grapheme('AŠ')
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
                Grapheme('BI'),
                Grapheme('BI')
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
        Grapheme('BI'),
        Grapheme('BI')
    ))
])
def test_splittable_grapheme_can_only_contain_graphemes(value):
    with pytest.raises(ValueError):
        SplittableGrapheme((value, Grapheme('BI')))
