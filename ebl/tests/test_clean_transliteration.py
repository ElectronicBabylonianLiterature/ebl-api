from ebl.fragmentarium.transliterations import clean


def test_ignored_lines():
    transliteration = '&K11111\n@reverse\n\n$ end of side\n#note\n=: foo'
    assert clean(transliteration) == []


def test_strip_line_numbers():
    transliteration = '1. mu\n2\'. me\na+1. e\n1.2. a'
    assert clean(transliteration) == [
        'mu',
        'me',
        'e',
        'a'
    ]


def test_map_spaces():
    transliteration = ('1. šu-mu gid₂-ba\n'
                       '2. {giš}BI.IS\n'
                       '3. {giš}|BI.IS|\n'
                       '4. {m}{d}\n'
                       '5. {+tu-um}\n'
                       '6. tu | na\n'
                       '6. tu & na\n'
                       '6. tu &2 na\n'
                       '7. & e\n'
                       '7. e &\n'
                       '7. | e\n'
                       '7. e |\n'
                       '8. mu {{giš}}BI\n'
                       '9. din-{d}x\n'
                       '10. šu+mu\n'
                       '11. {d}+a')

    assert clean(transliteration) == [
        'šu mu gid₂ ba',
        'giš bi is',
        'giš |BI.IS|',
        'm d',
        'tu um',
        'tu na',
        'tu na',
        'tu na',
        'e',
        'e',
        'e',
        'e',
        'mu giš bi',
        'din d x',
        'šu mu',
        'd a'
    ]


def test_strip_lacuna():
    transliteration = ('1. [... N]U KU₃\n'
                       '2. [... a]-ba-an\n'
                       '3. [...] ši [...]\n'
                       '5. [(... a)]-ba\n'
                       '6. [x (x) x]\n'
                       '7. [(x) (x)]\n'
                       '8. [(...)]')
    assert clean(transliteration) == [
        'nu ku₃',
        'a ba an',
        'ši',
        'a ba',
        'x x x',
        'x x',
        ''
    ]


def test_indent():
    transliteration = '1. ($___$) ša₂'
    assert clean(transliteration) == [
        'ša₂'
    ]


def test_strip_flags():
    transliteration =\
        '1.  ba! ba? ba# ba*\n2. $KU'
    assert clean(transliteration) == [
        'ba ba ba ba',
        'ku'
    ]


def test_strip_shifts():
    transliteration =\
        '1. %es qa\n2. ba %g ba'
    assert clean(transliteration) == [
        'qa',
        'ba ba'
    ]


def test_strip_omissions():
    transliteration =\
        '1.  <NU> KU₃\n2. <(ba)> an\n5. <<a>> ba'
    assert clean(transliteration) == [
        'ku₃',
        'an',
        'ba'
    ]


def test_min():
    transliteration =\
        '3. MIN<(an)> ši'
    assert clean(transliteration) == [
        'min ši'
    ]


def test_numbers():
    transliteration =\
        '1. 1(AŠ)\n2. 1 2 10 20 30\n3. 256'
    assert clean(transliteration) == [
        '1(AŠ)',
        '1 2 10 20 30',
        '256'
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

    transliteration = '\n'.join([
        f'{index}. {grapheme}'
        for index, grapheme in enumerate(graphemes)
    ])

    assert clean(transliteration) == graphemes


def test_lower_case():
    transliteration = ('1. gid₂\n'
                       '2. ši\n'
                       '3. BI\n'
                       '4. BI.IS\n'
                       '4. BI+IS\n'
                       '5. |BI.IS|\n'
                       '6. DIŠ\n'
                       '7. KU₃\n'
                       '8. ku(KU₃)\n'
                       '9. ku/|BI×IS|')

    assert clean(transliteration) == [
        'gid₂',
        'ši',
        'bi',
        'bi is',
        'bi is',
        '|BI.IS|',
        'diš',
        'ku₃',
        'ku(KU₃)',
        'ku/|BI×IS|'
    ]


def test_strip_at():
    transliteration = ('1. lu₂@v\n'
                       '2. LU₂@v\n'
                       '3. TA@v')

    assert clean(transliteration) == [
        'lu₂',
        'lu₂',
        'ta'
    ]
