from ebl.fragmentarium.transliteration_to_signs import clean_transliteration


def test_ignored_lines():
    transliteration = '@reverse\n\n$ end of side\n#note'
    assert clean_transliteration(transliteration) == []


def test_strip_line_numbers():
    transliteration = '1. mu\n2\'. me\n3. %es qa'
    assert clean_transliteration(transliteration) == [
        'mu',
        'me',
        'qa'
    ]


def test_map_spaces():
    transliteration =\
        '1. šu-mu gid₂-ba\n2. {giš}BI.IS\n3. {m}{d}\n4. {+tu-um}\n5. tu | na'
    assert clean_transliteration(transliteration) == [
        'šu mu gid₂ ba',
        'giš BI IS',
        'm d',
        'tu um',
        'tu na'
    ]


def test_strip_lacuna():
    transliteration =\
        '1.  [... N]U KU₃\n2. [... a]-ba-an\n3. [...] ši [...]\n5. [(... a)]-ba'
    assert clean_transliteration(transliteration) == [
        'KU₃',
        'ba an',
        'ši',
        'ba'
    ]


def test_indent():
    transliteration = '1. ($___$) ša₂'
    assert clean_transliteration(transliteration) == [
        'ša₂'
    ]

def test_strip_flags():
    transliteration =\
        '1.  ba! ba? ba# ba*\n2. $KU'
    assert clean_transliteration(transliteration) == [
        'ba ba ba ba',
        'KU'
    ]
