from ebl.atf.atf import Atf
from ebl.fragmentarium.domain.fragment_info import FragmentInfo
from ebl.tests.factories.fragment import TransliteratedFragmentFactory
from ebl.transliteration_search.transliteration_query import \
    TransliterationQuery
from ebl.transliteration_search.value import ValueFactory


def test_convert_atf_to_signs(transliteration_search, sign_list, signs):
    for sign in signs:
        sign_list.create(sign)

    atf = Atf('1. šu gid₂')

    assert transliteration_search.convert_atf_to_signs(atf) == 'ŠU BU'


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
        [ValueFactory.create_grapheme('|(4×ZA)×KUR|'),
         ValueFactory.create_grapheme('|(AŠ&AŠ@180)×U|'),
         ValueFactory.create_grapheme('NU')],
        [ValueFactory.create_reading('ummu', 3),
         ValueFactory.create_splittable_grapheme('|IGI.KU|'),
         ValueFactory.create_reading('mat', 3)],
        [ValueFactory.create_splittable_grapheme('|A.EDIN.LAL|'),
         ValueFactory.create_splittable_grapheme('|HU.HI|'),
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
        ['KU', 'BU', 'ABZ075', 'ABZ207a\\u002F207b\\u0020X'],
        ['ABZ531+588', '|(AŠ&AŠ@180)×U|', 'ABZ075'],
        ['A', 'ABZ168', 'LAL', 'ABZ207a\\u002F207b\\u0020X', 'KU', 'HU', 'HI'],
        ['A', 'ABZ168', 'LAL', 'HU', 'HI', 'ABZ075', 'KU', 'NU×SI'],
        ['ABZ207a\\u002F207b\\u0020X/MA'],
        ['?', '?', 'X'],
        ['ABZ001', 'DIŠ', '2', 'ABZ411', 'ABZ411', 'ABZ411', '30', '256'],
    ]


def test_search(transliteration_search, fragment_repository, when):
    transliterated_fragment = TransliteratedFragmentFactory.build()
    sign_matrix = [['MA', 'UD']]
    query = TransliterationQuery(sign_matrix)
    matching_fragments = [transliterated_fragment]

    (when(fragment_repository)
     .search_signs(query)
     .thenReturn(matching_fragments))

    expected_lines = (('6\'. [...] x mu ta-ma-tu₂',),)
    expected = [
        FragmentInfo.of(fragment, expected_lines)
        for fragment in matching_fragments
    ]
    assert transliteration_search.search(query) == expected
