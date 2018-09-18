from ebl.fragmentarium.transliterations import filter_lines


def test_filter_lines():
    transliteration =\
        '&K11111\n@reverse\n\n$ end of side\n#note\n=: foo\n1. ku\n2. $AN'
    assert filter_lines(transliteration) == ['1. ku', '2. $AN']
