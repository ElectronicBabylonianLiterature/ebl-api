from ebl.fragment.value import ValueFactory
from ebl.text.atf import UNIDENTIFIED_SIGN


def test_create_and_find(sign_list, signs):
    sign_name = sign_list.create(signs[0])

    assert sign_list.find(sign_name) == signs[0]


def test_search(sign_list, signs):
    sign_list.create(signs[0])
    sign_list.create(signs[1])

    assert sign_list.search(
        signs[0].values[0].value,
        signs[0].values[0].sub_index
    ) == signs[0]


def test_map_readings(sign_list, signs):
    for sign in signs:
        sign_list.create(sign)

    values = [
        [ValueFactory.create_reading('ku', 1),
         ValueFactory.create_reading('gid', 2),
         ValueFactory.create_reading('nu', 1),
         ValueFactory.create_reading('ši', 1)],
        [ValueFactory.create_not_reading('|BI×IS|'),
         ValueFactory.create_not_reading('BI')],
        [ValueFactory.create_variant((ValueFactory.create_reading('ši', 1),
                                      ValueFactory.create_reading('ma', 1)))],
        [ValueFactory.create_reading('unknown', 1),
         ValueFactory.create_not_reading(UNIDENTIFIED_SIGN)],
        [ValueFactory.create_not_reading('AŠ'),
         ValueFactory.create_number('1'),
         ValueFactory.create_number('2'), ValueFactory.create_number('10'),
         ValueFactory.create_number('20'), ValueFactory.create_number('30'),
         ValueFactory.create_number('256')]
    ]
    mapped_signs = sign_list.map_readings(values)

    assert mapped_signs == [
        ['KU', 'BU', 'ABZ075', 'ABZ207a\\u002F207b'],
        ['|BI×IS|', 'BI'],
        ['ABZ207a\\u002F207b/MA'],
        ['?', 'X'],
        ['AŠ', 'DIŠ', '2', 'U', '20', '30', '256'],
    ]
