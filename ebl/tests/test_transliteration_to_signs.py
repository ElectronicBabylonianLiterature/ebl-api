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
        '1. šu-mu gid₂-ba\n2. {giš}BI.IS\n3. {m}{d}\n4. {+tu-um}'
    assert clean_transliteration(transliteration) == [
        'šu mu gid₂ ba',
        'giš BI IS',
        'm d',
        'tu um'
    ]


def test_map_readings():
    transliteration =\
        '1.  [... N]U KU₃\n2. [... a]-ba-an\n3. [...] ši [...]'
    assert clean_transliteration(transliteration) == [
        'KU₃',
        'ba an',
        'ši'
    ]


def test_indent():
    transliteration = '1. ($___$) ša₂'
    assert clean_transliteration(transliteration) == [
        'ša₂'
    ]
