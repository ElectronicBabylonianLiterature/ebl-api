from ebl.text.atf import Atf
from ebl.transliteration_search.value import ValueFactory


def test_convert_to_signs(transliteration_search, sign_list, signs):
    for sign in signs:
        sign_list.create(sign)

    atf = Atf('1. šu gid₂')

    assert transliteration_search.convert_atf_to_signs(atf) == 'ŠU BU'


def test_map_readings(transliteration_search, sign_repository, signs):
    for sign in signs:
        sign_repository.create(sign)

    values = [
        [ValueFactory.create_reading('ku', 1),
         ValueFactory.create_reading('gid', 2),
         ValueFactory.create_reading('nu', 1),
         ValueFactory.create_reading('ši', 1),
         ValueFactory.create_reading('ummu', 3),
         ValueFactory.create_reading('mat', 3)],
        [ValueFactory.create_grapheme('|(4×ZA)×KUR|'),
         ValueFactory.create_grapheme('|(AŠ&AŠ@180)×U|'),
         ValueFactory.create_grapheme('NU')],
        [ValueFactory.create_splittable_grapheme('|A.EDIN.LAL|'),
         ValueFactory.create_splittable_grapheme('|NU.KU.NU×SI|')],
        [ValueFactory.create_variant((ValueFactory.create_reading('ši', 1),
                                      ValueFactory.create_reading('ma', 1)))],
        [ValueFactory.create_reading('unknown', 1),
         ValueFactory.INVALID,
         ValueFactory.UNIDENTIFIED],
        [ValueFactory.create_grapheme('AŠ'),
         ValueFactory.create_number('1'),
         ValueFactory.create_number('2'),
         ValueFactory.create_number('10'),
         ValueFactory.create_number('20'),
         ValueFactory.create_number('30'),
         ValueFactory.create_number('256')]
    ]
    mapped_signs = transliteration_search.convert_values_to_signs(values)

    assert mapped_signs == [
        ['KU', 'BU', 'ABZ075', 'ABZ207a\\u002F207b\\u0020X', '|A.EDIN.LAL|',
         'ABZ081'],
        ['ABZ531+588', '|(AŠ&AŠ@180)×U|', 'ABZ075'],
        ['A', 'EDIN', 'LAL', 'ABZ075', 'KU', 'NU×SI'],
        ['ABZ207a\\u002F207b\\u0020X/MA'],
        ['?', '?', 'X'],
        ['ABZ001', 'DIŠ', '2', 'ABZ411', 'ABZ471', '30', '256'],
    ]
