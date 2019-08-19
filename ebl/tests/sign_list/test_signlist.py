def test_create_and_find(sign_list, signs):
    sign_name = sign_list.create(signs[0])

    assert sign_list.find(sign_name) == signs[0]


def test_search(sign_list, signs):
    sign_list.create(signs[0])
    sign_list.create(signs[1])

    assert sign_list.search(
        signs[0]['values'][0]['value'],
        signs[0]['values'][0]['subIndex']
    ) == signs[0]


def test_transliteration_to_signs(sign_list, signs):
    for sign in signs:
        sign_list.create(sign)

    clean_transliteration = [
        'šu gid₂ |BI×IS| BI',
        'šu/gid₂',
        'unknown x X',
        '1(AŠ) 1 2 10 20 30 256',
        ''
    ]
    mapped_signs = sign_list.map_transliteration(clean_transliteration)

    assert mapped_signs == [
        ['ŠU', 'BU', '|BI×IS|', 'BI'],
        ['ŠU/BU'],
        ['?', 'X', 'X'],
        ['AŠ', 'DIŠ', '2', 'U', '20', '30', '256'],
        ['']
    ]
