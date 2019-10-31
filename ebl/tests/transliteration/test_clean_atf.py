import pytest

from ebl.transliteration.domain.atf import Atf
from ebl.transliteration.domain.clean_atf import CleanAtf


def test_atf():
    atf = Atf('1. kur')

    assert CleanAtf(atf).atf == atf


def test_filtered():
    clean_atf = CleanAtf(
        Atf('&K11111\n@reverse\n\n$ end of side\n#note\n=: foo\n1. ku\n2. $AN')
    )
    assert clean_atf.filtered == ['1. ku', '2. $AN']


def test_ignored_lines():
    clean_atf = CleanAtf(Atf(
        '&K11111\n'
        '@reverse\n'
        '\n'
        '$ end of side\n'
        '$single ruling\n'
        '$ single ruling\n'
        '$double ruling\n'
        '$ double ruling\n'
        '$triple ruling\n'
        '$ triple ruling\n'
        '$ (random text)\n'
        '#note\n=: foo'
    ))
    assert clean_atf.cleaned == []


def test_strip_line_numbers():
    clean_atf = CleanAtf(Atf(
        '1. mu\n2\'. me\na+1. e\n1.2. a\n11\'-12\'. kur. ra'
    ))
    assert clean_atf.cleaned == [
        ['mu'],
        ['me'],
        ['e'],
        ['a'],
        ['kur', 'ra']
    ]


def test_map_spaces():
    clean_atf = CleanAtf(Atf(
        '1. šu-mu gid₂+ba šu.mu gid₂:ba\n'
        '2. {giš}BI.IS\n'
        '3. {giš}|BI.IS|\n'
        '4. {m}{d}\n'
        '5. {+tu-um}\n'
        '6. tu | na\n'
        '6. nibru{ki} | na\n'
        '6. nibru{{ki}} | na\n'
        '6. mu | {giš}BI\n'
        '6. mu | {{giš}}BI\n'
        '6. tu & na\n'
        '6. tu &2 na\n'
        '7. & e\n'
        '7. e &\n'
        '7. | e\n'
        '7. e |\n'
        '8. mu {{giš}}BI\n'
        '9. din-{d}x\n'
        '10. šu+mu\n'
        '11. {d}+a'
    ))

    assert clean_atf.cleaned == [
        ['šu', 'mu', 'gid₂', 'ba', 'šu', 'mu', 'gid₂', 'ba'],
        ['giš', 'bi', 'is'],
        ['giš', '|BI.IS|'],
        ['m', 'd'],
        ['tu', 'um'],
        ['tu', 'na'],
        ['nibru', 'ki', 'na'],
        ['nibru', 'ki', 'na'],
        ['mu', 'giš', 'bi'],
        ['mu', 'giš', 'bi'],
        ['tu', 'na'],
        ['tu', 'na'],
        ['e'],
        ['e'],
        ['e'],
        ['e'],
        ['mu', 'giš', 'bi'],
        ['din', 'd', 'x'],
        ['šu', 'mu'],
        ['d', 'a']
    ]


def test_strip_lacuna():
    clean_atf = CleanAtf(Atf(
        '1. [... N]U KU₃\n'
        '2. [... a]-ba-an\n'
        '3. [...] ši [...]\n'
        '5. [(... a)]-ba\n'
        '6. [x (x) x]\n'
        '7. [(x) (x)]\n'
        '8. [(...)]\n'
        '9. ⸢ba⸣'
    ))
    assert clean_atf.cleaned == [
        ['nu', 'ku₃'],
        ['a', 'ba', 'an'],
        ['ši'],
        ['a', 'ba'],
        ['x', 'x', 'x'],
        ['x', 'x'],
        [''],
        ['ba']
    ]


def test_indent():
    clean_atf = CleanAtf(Atf('1. ($___$) ša₂'))
    assert clean_atf.cleaned == [
        ['ša₂']
    ]


def test_strip_flags():
    clean_atf =\
        CleanAtf(Atf('1.  ba! ba? ba# ba*\n2. $KU'))
    assert clean_atf.cleaned == [
        ['ba', 'ba', 'ba', 'ba'],
        ['ku']
    ]


def test_strip_shifts():
    clean_atf =\
        CleanAtf(Atf('1. %es qa\n2. ba %g ba'))
    assert clean_atf.cleaned == [
        ['qa'],
        ['ba', 'ba']
    ]


def test_strip_commentary_protocols():
    clean_atf =\
        CleanAtf(Atf('1. !qt qa !zz\n2. ba !cm ba !bs'))
    assert clean_atf.cleaned == [
        ['qa'],
        ['ba', 'ba']
    ]


def test_strip_omissions():
    clean_atf = CleanAtf(Atf(
        '1.  <NU> KU₃\n2. <(ba)> an\n5. <<a>> ba'
    ))
    assert clean_atf.cleaned == [
        ['ku₃'],
        ['an'],
        ['ba']
    ]


def test_min():
    clean_atf =\
        CleanAtf(Atf('3. MIN<(an)> ši'))
    assert clean_atf.cleaned == [
        ['min', 'ši']
    ]


def test_numbers():
    clean_atf =\
        CleanAtf(Atf('1. 1(AŠ)\n2. 1 2 10 20 30\n3. 256'))
    assert clean_atf.cleaned == [
        ['1(AŠ)'],
        ['1', '2', '10', '20', '30'],
        ['256']
    ]


def test_graphemes():
    graphemes = [
        '|BIxIS|',
        '|BI×IS|',
        '|BI.IS|',
        '|BI+IS|',
        '|BI&IS|',
        '|BI%IS|',
        '|BI@IS|',
        '|3×BI|',
        '|3xBI|',
        '|GEŠTU~axŠE~a@t|',
        '|(GI&GI)×ŠE₃|',
        '|UD.AB@g|'
    ]

    clean_atf = CleanAtf(Atf('\n'.join([
        f'{index}. {grapheme}'
        for index, grapheme in enumerate(graphemes)
    ])))

    assert clean_atf.cleaned == [[grapheme] for grapheme in graphemes]


def test_lower_case():
    clean_atf = CleanAtf(Atf(
        '1. gid₂\n'
        '2. ši\n'
        '3. BI\n'
        '4. BI.IS\n'
        '4. BI+IS\n'
        '5. |BI.IS|\n'
        '6. DIŠ\n'
        '7. KU₃\n'
        '8. ku(KU₃)\n'
        '9. ku/|BI×IS|'
    ))

    assert clean_atf.cleaned == [
        ['gid₂'],
        ['ši'],
        ['bi'],
        ['bi', 'is'],
        ['bi', 'is'],
        ['|BI.IS|'],
        ['diš'],
        ['ku₃'],
        ['ku(KU₃)'],
        ['ku/|BI×IS|']
    ]


def test_strip_at():
    clean_atf = CleanAtf(Atf(
        '1. lu₂@v\n'
        '2. LU₂@v\n'
        '3. TA@v'
    ))

    assert clean_atf.cleaned == [
        ['lu₂'],
        ['lu₂'],
        ['ta']
    ]


def test_strip_line_continuation():
    clean_atf = CleanAtf(Atf(
        '1. ku →'
    ))

    assert clean_atf.cleaned == [
        ['ku']
    ]


@pytest.mark.parametrize('erasure,cleaned', [
    ('1. °\\° ku', ['ku']),
    ('°\\°  ku', ['ku']),
    ('1. °ra (ra) 1(AŠ) <(ra)> [(ra)]\\° ku', ['ku']),
    ('1. °<(1(AŠ))>\\° 2(DIŠ)', ['2(DIŠ)']),
    ('1. °[(1(AŠ))]\\° 2(DIŠ)', ['2(DIŠ)']),
    ('1. °\\ra° ku', ['ra', 'ku']),
    ('1. °ra\\ku°', ['ku']),
    ('1. °\\KU°', ['ku'])
])
def test_strip_erasure(erasure, cleaned):
    clean_atf = CleanAtf(Atf(erasure))

    assert clean_atf.cleaned == [cleaned]


@pytest.mark.parametrize('atf,cleaned', [
    ('1. & qa\n2. ba &3 ba', [
        ['qa'],
        ['ba', 'ba'],
    ]),
    ('1. [...] & [...] & x [...]', [['x']]),
    ('1. [...] & [...] &2 x [...]', [['x']]),
    ('1. [...] &2 [...] & x [...]', [['x']]),
    ('1. [...] &2 [...] &3 x [...]', [['x']]),
    ('1. [...] | [...] | x [...]', [['x']]),
    ('1. | x [...]', [['x']]),
    ('1. x |', [['x']]),
    ('1. x  &  x', [['x', 'x']]),
])
def test_strip_dividers(atf, cleaned):
    clean_atf =\
        CleanAtf(Atf(atf))
    assert clean_atf.cleaned == cleaned
