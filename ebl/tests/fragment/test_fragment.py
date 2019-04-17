import attr
import pytest
from freezegun import freeze_time

from ebl.fragment.folios import Folio, Folios
from ebl.fragment.fragment import Fragment, Measure, UncuratedReference
from ebl.fragment.transliteration import (
    Transliteration, TransliterationError
)
from ebl.fragment.transliteration_query import TransliterationQuery
from ebl.tests.factories.bibliography import ReferenceFactory
from ebl.tests.factories.fragment import (
    FragmentFactory, TransliteratedFragmentFactory
)
from ebl.tests.factories.record import RecordFactory
from ebl.text.atf_parser import parse_atf
from ebl.text.lemmatization import Lemmatization, LemmatizationError
from ebl.text.text import Text


def test_to_dict_for(user):
    fragment = FragmentFactory.build()
    assert fragment.to_dict_for(user) == {
        **fragment.to_dict(),
        'folios': fragment.folios.filter(user).to_list()
    }


def test_number():
    fragment = FragmentFactory.build(number='1')
    assert fragment.number == '1'


def test_accession():
    fragment = FragmentFactory.build(accession='accession-3')
    assert fragment.accession == 'accession-3'


def test_cdli_number():
    fragment = FragmentFactory.build(cdli_number='cdli-4')
    assert fragment.cdli_number == 'cdli-4'


def test_bm_id_number():
    fragment = FragmentFactory.build(bm_id_number='bmId-2')
    assert fragment.bm_id_number == 'bmId-2'


def test_publication():
    fragment = FragmentFactory.build(publication='publication')
    assert fragment.publication == 'publication'


def test_description():
    fragment = FragmentFactory.build(description='description')
    assert fragment.description == 'description'


def test_collection():
    fragment = FragmentFactory.build(collection='Collection')
    assert fragment.collection == 'Collection'


def test_script():
    fragment = FragmentFactory.build(script='NA')
    assert fragment.script == 'NA'


def test_museum():
    fragment = FragmentFactory.build(museum='Museum')
    assert fragment.museum == 'Museum'


def test_length():
    fragment = FragmentFactory.build()
    assert fragment.length == Measure()


def test_width():
    fragment = FragmentFactory.build()
    assert fragment.width == Measure()


def test_thickness():
    fragment = FragmentFactory.build()
    assert fragment.thickness == Measure()


def test_joins():
    fragment = FragmentFactory.build()
    assert fragment.joins == tuple()


def test_notes():
    fragment = FragmentFactory.build()
    assert fragment.notes == ''


def test_signs():
    transliterated_fragment = TransliteratedFragmentFactory.build()
    assert transliterated_fragment.signs == (
        'KU NU IGI\n'
        'MI DIŠ UD ŠU\n'
        'KI DU U BA MA TI\n'
        'X MU TA MA UD\n'
        'ŠU/|BI×IS|'
    )


def test_signs_none():
    fragment = FragmentFactory.build()
    assert fragment.signs is None


def test_record():
    record = RecordFactory.build()
    fragment = Fragment('X.1', record=record)
    assert fragment.record == record


def test_folios():
    fragment = FragmentFactory.build()
    assert fragment.folios == Folios((
        Folio('WGL', '1'),
        Folio('XXX', '1')
    ))


def test_text():
    fragment = FragmentFactory.build()
    assert fragment.text == Text()


def test_uncurated_references():
    uncurated_references = (
        UncuratedReference('7(0)'),
        UncuratedReference('CAD 51', (34, 56)),
        UncuratedReference('7(1)')
    )
    fragment = FragmentFactory.build(uncurated_references=uncurated_references)
    assert fragment.uncurated_references == uncurated_references


def test_uncurated_references_none():
    fragment = FragmentFactory.build()
    assert fragment.uncurated_references is None


def test_references():
    reference = RecordFactory.build()
    fragment = FragmentFactory.build(references=(reference,))
    assert fragment.references == (reference,)


def test_references_default():
    fragment = FragmentFactory.build()
    assert fragment.references == tuple()


@freeze_time("2018-09-07 15:41:24.032")
def test_add_transliteration(user):
    fragment = FragmentFactory.build()
    atf = '1. x x'
    transliteration = Transliteration(atf, fragment.notes)
    text = parse_atf(atf)
    record = fragment.record.add_entry('', atf, user)

    updated_fragment = fragment.update_transliteration(
        transliteration,
        user
    )
    expected_fragment = attr.evolve(fragment, text=text, record=record)

    assert updated_fragment == expected_fragment


@freeze_time("2018-09-07 15:41:24.032")
def test_update_transliteration(lemmatized_fragment, user):
    lines = lemmatized_fragment.text.atf.split('\n')
    lines[1] = '2\'. [...] GI₆ mu u₄-š[u ...]'
    atf = '\n'.join(lines)
    text = parse_atf(atf)
    transliteration =\
        Transliteration(atf, 'updated notes', 'X X\nX')
    updated_fragment = lemmatized_fragment.update_transliteration(
        transliteration,
        user
    )

    expected_fragment = attr.evolve(
        lemmatized_fragment,
        text=lemmatized_fragment.text.merge(text),
        notes=transliteration.notes,
        signs=transliteration.signs,
        record=lemmatized_fragment.record.add_entry(
            lemmatized_fragment.text.atf,
            transliteration.atf,
            user
        )
    )

    assert updated_fragment == expected_fragment


def test_test_update_transliteration_invalid_value(user):
    fragment = FragmentFactory.build()
    atf = '1. x\ninvalid line'
    transliteration = Transliteration(atf, fragment.notes)

    with pytest.raises(TransliterationError,
                       match='Invalid transliteration') as excinfo:
        fragment.update_transliteration(
            transliteration,
            user
        )

    assert excinfo.value.errors == [
        {
            'description': 'Invalid line',
            'lineNumber': 2
        }
    ]


def test_update_notes(user):
    fragment = FragmentFactory.build()
    transliteration =\
        Transliteration(fragment.text.atf, 'new notes')
    updated_fragment = fragment.update_transliteration(
        transliteration,
        user
    )

    expected_fragment = attr.evolve(
        fragment,
        notes=transliteration.notes
    )

    assert updated_fragment == expected_fragment


@pytest.mark.parametrize("sign_matrix,lines", [
    ([['DIŠ', 'UD']], [
        ['2\'. [...] GI₆ ana u₄-š[u ...]']
    ]),
    ([['KU']], [
        ['1\'. [...-ku]-nu-ši [...]']
    ]),
    ([['UD']], [
        ['2\'. [...] GI₆ ana u₄-š[u ...]'],
        ['6\'. [...] x mu ta-ma-tu₂']
    ]),
    ([['MI', 'DIŠ'], ['U', 'BA', 'MA']], [
        [
            '2\'. [...] GI₆ ana u₄-š[u ...]',
            '3\'. [... k]i-du u ba-ma-t[i ...]'
        ]
    ]),
    ([['IGI', 'UD']], [])
])
def test_add_matching_lines(sign_matrix, lines):
    transliterated_fragment = TransliteratedFragmentFactory.build()
    query = TransliterationQuery(sign_matrix)
    with_matching_lines =\
        transliterated_fragment.add_matching_lines(query)

    assert with_matching_lines.to_dict() == {
        **transliterated_fragment.to_dict(),
        'matching_lines': lines
    }


def test_update_lemmatization():
    transliterated_fragment = TransliteratedFragmentFactory.build()
    tokens = transliterated_fragment.text.lemmatization.to_list()
    tokens[1][1]['uniqueLemma'] = ['nu I']
    lemmatization = Lemmatization.from_list(tokens)
    expected = attr.evolve(
        transliterated_fragment,
        text=transliterated_fragment.text.update_lemmatization(lemmatization)
    )

    assert transliterated_fragment.update_lemmatization(lemmatization) ==\
        expected


def test_update_lemmatization_incompatible():
    fragment = FragmentFactory.build()
    lemmatization = Lemmatization.from_list(
        [[{'value': 'mu', 'uniqueLemma': []}]]
    )
    with pytest.raises(LemmatizationError):
        fragment.update_lemmatization(lemmatization)


def test_set_references():
    fragment = FragmentFactory.build()
    references = (ReferenceFactory.build(),)
    updated_fragment = fragment.set_references(references)

    assert updated_fragment.references == references
