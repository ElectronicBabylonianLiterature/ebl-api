from ebl.fragmentarium.ngrams import to_ngrams


def test_to_ngrams():
    signs = [
        ['ŠU', 'BU', 'BI', 'IS'],
        ['|BIxIS|', 'TUKUL', 'AŠ'],
        ['U']
    ]

    assert to_ngrams(signs) == {'ŠUBUBI', 'BUBIIS', 'ŠUBUBIIS', '|BIxIS|TUKULAŠ', 'U'}
