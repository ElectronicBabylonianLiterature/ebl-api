from ebl.atf.domain.atf import Atf
from ebl.signs.domain.sign import SignName
from ebl.signs.domain.value import Grapheme, NotReading, Reading, ValueFactory


def test_convert_atf_to_sign_matrix(transliteration_search, sign_list, signs):
    for sign in signs:
        sign_list.create(sign)

    atf = Atf('1. šu gid₂')

    assert transliteration_search.convert_atf_to_sign_matrix(atf) ==\
        [['ŠU', 'BU']]


def test_convert_atf_to_values(transliteration_search):
    atf = Atf(
        '&K11111\n'
        '@reverse\n'
        '\n'
        '$ end of side\n'
        '#note\n'
        '=: foo\n'
        '1. ku X x\n'
        '2. $AN |BI×IS|\n'
        '3. nuₓ'
    )
    assert transliteration_search.convert_atf_to_values(atf) == [
        [Reading('ku', 1, '?'), NotReading('X'), NotReading('X')],
        [Reading('an', 1, '?'), Grapheme(SignName('|BI×IS|'))],
        [NotReading('?')]
    ]


def test_convert_values_to_signs(transliteration_search,
                                 sign_repository,
                                 signs):
    for sign in signs:
        sign_repository.create(sign)

    values = [
        [ValueFactory.create_reading('ku', 1),
         ValueFactory.create_reading('gid', 2),
         ValueFactory.create_reading('nu', 1),
         ValueFactory.create_reading('ši', 1)],
        [ValueFactory.create_grapheme(SignName('|(4×ZA)×KUR|')),
         ValueFactory.create_grapheme(SignName('|(AŠ&AŠ@180)×U|')),
         ValueFactory.create_grapheme(SignName('NU'))],
        [ValueFactory.create_reading('ummu', 3),
         ValueFactory.create_splittable_grapheme('|IGI.KU|'),
         ValueFactory.create_reading('mat', 3)],
        [ValueFactory.create_splittable_grapheme('|A.EDIN.LAL|'),
         ValueFactory.create_splittable_grapheme('|HU.HI|'),
         ValueFactory.create_splittable_grapheme('|NU.KU.NU×SI|')],
        [ValueFactory.create_variant((ValueFactory.create_reading('ši', 1),
                                      ValueFactory.create_reading('ma', 1))),
         ValueFactory.create_variant((ValueFactory.create_reading('ku', 1),
                                      ValueFactory.create_reading('ummu', 3),
                                      ValueFactory.create_reading('mat', 3)))
         ],
        [ValueFactory.create_reading('unknown', 1),
         ValueFactory.INVALID,
         ValueFactory.UNIDENTIFIED],
        [ValueFactory.create_grapheme(SignName('AŠ')),
         ValueFactory.create_number('1'),
         ValueFactory.create_number('2'),
         ValueFactory.create_number('10'),
         ValueFactory.create_number('20'),
         ValueFactory.create_number('30'),
         ValueFactory.create_number('256')]
    ]
    mapped_signs = transliteration_search.convert_values_to_signs(values)

    assert mapped_signs == [
        ['KU', 'BU', 'ABZ075', 'ABZ207a\\u002F207b\\u0020X'],
        ['ABZ531+588', '|(AŠ&AŠ@180)×U|', 'ABZ075'],
        ['A', 'ABZ168', 'LAL', 'ABZ207a\\u002F207b\\u0020X', 'KU', 'HU', 'HI'],
        ['A', 'ABZ168', 'LAL', 'HU', 'HI', 'ABZ075', 'KU', 'NU×SI'],
        ['ABZ207a\\u002F207b\\u0020X/MA', 'KU/|A.EDIN.LAL|/ABZ081'],
        ['?', '?', 'X'],
        ['ABZ001', 'DIŠ', '2', 'ABZ411', 'ABZ411', 'ABZ411', '30', '256'],
    ]
