import attr
from freezegun import freeze_time
import pytest
from ebl.text.atf_parser import parse_atf
from ebl.fragment.fragment import Measure, UncuratedReference
from ebl.fragment.folios import Folios, Folio
from ebl.fragment.record import (
    RecordType,
    RecordEntry,
    Record
)
from ebl.text.text import Text
from ebl.text.lemmatization import Lemmatization, LemmatizationError
from ebl.fragment.transliteration import (
    Transliteration, TransliterationError
)
from ebl.fragment.transliteration_query import TransliterationQuery


def test_to_dict_for(fragment, user):
    assert fragment.to_dict_for(user) == {
        **fragment.to_dict(),
        'folios': fragment.folios.filter(user).to_list()
    }


def test_number(fragment):
    assert fragment.number == '1'


def test_accession(fragment):
    assert fragment.accession == 'accession-3'


def test_cdli_number(fragment):
    assert fragment.cdli_number == 'cdli-4'


def test_bm_id_number(fragment):
    assert fragment.bm_id_number == 'bmId-2'


def test_publication(fragment):
    assert fragment.publication == 'publication'


def test_description(fragment):
    assert fragment.description == 'description'


def test_collection(fragment):
    assert fragment.collection == 'Collection'


def test_script(fragment):
    assert fragment.script == 'NA'


def test_museum(fragment):
    assert fragment.museum == 'Museum'


def test_length(fragment):
    assert fragment.length == Measure()


def test_width(fragment):
    assert fragment.width == Measure()


def test_thickness(fragment):
    assert fragment.thickness == Measure()


def test_joins(fragment):
    assert fragment.joins == tuple()


def test_notes(fragment):
    assert fragment.notes == ''


def test_signs(transliterated_fragment):
    assert transliterated_fragment.signs == (
        'KU NU IGI\n'
        'MI DIŠ UD ŠU\n'
        'KI DU U BA MA TI\n'
        'X MU TA MA UD\n'
        'ŠU/|BI×IS|'
    )


def test_signs_none(fragment):
    assert fragment.signs is None


def test_record(transliterated_fragment):
    assert transliterated_fragment.record == Record((
        RecordEntry(
            'Tester',
            RecordType.TRANSLITERATION,
            '2018-12-21T17:05:27.352435'
        ),
    ))


def test_folios(fragment):
    assert fragment.folios == Folios((
        Folio('WGL', '1'),
        Folio('XXX', '1')
    ))


def test_text(fragment):
    assert fragment.text == Text()


def test_uncurated_references(interesting_fragment):
    assert interesting_fragment.uncurated_references == (
        UncuratedReference('7(0)'),
        UncuratedReference('CAD 51', (34, 56)),
        UncuratedReference('7(1)')
    )


def test_uncurated_references_none(fragment):
    assert fragment.uncurated_references is None


def test_references(transliterated_fragment, reference):
    assert transliterated_fragment.references == (reference,)


def test_references_default(fragment):
    assert fragment.references == tuple()


@freeze_time("2018-09-07 15:41:24.032")
def test_add_transliteration(fragment, user):
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


def test_test_update_transliteration_invalid_value(fragment, user):
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


def test_update_notes(fragment, user):
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
def test_add_matching_lines(sign_matrix, lines, transliterated_fragment):
    query = TransliterationQuery(sign_matrix)
    with_matching_lines =\
        transliterated_fragment.add_matching_lines(query)

    assert with_matching_lines.to_dict() == {
        **transliterated_fragment.to_dict(),
        'matching_lines': lines
    }


def test_update_lemmatization(transliterated_fragment):
    tokens = transliterated_fragment.text.lemmatization.to_list()
    tokens[1][1]['uniqueLemma'] = ['nu I']
    lemmatization = Lemmatization.from_list(tokens)
    expected = attr.evolve(
        transliterated_fragment,
        text=transliterated_fragment.text.update_lemmatization(lemmatization)
    )

    assert transliterated_fragment.update_lemmatization(lemmatization) ==\
        expected


def test_update_lemmatization_incompatible(fragment):
    lemmatization = Lemmatization.from_list(
        [[{'value': 'mu', 'uniqueLemma': []}]]
    )
    with pytest.raises(LemmatizationError):
        fragment.update_lemmatization(lemmatization)


def test_set_references(fragment, reference):
    references = (reference,)
    updated_fragment = fragment.set_references(references)

    assert updated_fragment.references == references
