import datetime
from freezegun import freeze_time
import pytest
from ebl.text.atf_parser import parse_atf
from ebl.fragmentarium.fragment import (
    Fragment, Folios, Folio, Text, Measure, Record, RecordEntry
)
from ebl.text.language import Language
from ebl.text.lemmatization import Lemmatization, LemmatizationError
from ebl.text.line import ControlLine, TextLine, EmptyLine
from ebl.text.token import Token, Word, LanguageShift
from ebl.fragmentarium.transliteration import (
    Transliteration, TransliterationError
)
from ebl.fragmentarium.transliteration_query import TransliterationQuery


def test_dict_serialization(lemmatized_fragment):
    new_fragment = Fragment.from_dict(lemmatized_fragment.to_dict())

    assert new_fragment == lemmatized_fragment


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
            'Transliteration',
            '2018-12-21T17:05:27.352435'
        ),
    ))


def test_folios(fragment):
    assert fragment.folios == Folios((
        Folio('WGL', '1'),
        Folio('XXX', '1')
    ))


def test_text(fragment):
    text = Text((
        ControlLine.of_single('@', Token('obverse')),
        TextLine.of_iterable('1.', [
            LanguageShift('%sux'), Word('bu', Language.SUMERIAN)
        ]),
        EmptyLine()
    ))
    data = {
        **fragment.to_dict(),
        'text': {
            'lines': [line.to_dict() for line in text.lines]
        }
    }
    assert Fragment.from_dict(data).text == text


def test_hits(another_fragment):
    assert another_fragment.hits == 5


def test_hits_none(fragment):
    assert fragment.hits is None


def test_references(transliterated_fragment, reference):
    assert transliterated_fragment.references == (reference,)


def test_references_default(fragment):
    assert fragment.references == tuple()


@freeze_time("2018-09-07 15:41:24.032")
def test_add_transliteration(fragment, user):
    atf = '1. x x'
    transliteration = Transliteration(atf, fragment.notes)
    text = parse_atf(atf)
    record = Record((
        RecordEntry(
            user.ebl_name,
            'Transliteration',
            datetime.datetime.utcnow().isoformat()
        ),
    ))

    updated_fragment = fragment.update_transliteration(
        transliteration,
        user
    )
    expected_fragment = Fragment.from_dict({
        **fragment.to_dict(),
        'text': text.to_dict(),
        'record': record.to_list()
    })

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

    expected_fragment = Fragment.from_dict({
        **lemmatized_fragment.to_dict(),
        'text': lemmatized_fragment.text.merge(text).to_dict(),
        'notes': transliteration.notes,
        'signs': transliteration.signs,
        'record': lemmatized_fragment.record.add_entry(
            lemmatized_fragment.text.atf,
            transliteration.atf,
            user
        ).to_list()
    })

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

    expected_fragment = Fragment.from_dict({
        **fragment.to_dict(),
        'notes': transliteration.notes
    })

    assert updated_fragment == expected_fragment


def test_add_matching_lines(transliterated_fragment):
    query = TransliterationQuery([['MA', 'UD']])
    with_matching_lines =\
        transliterated_fragment.add_matching_lines(query)

    assert with_matching_lines.to_dict() == {
        **transliterated_fragment.to_dict(),
        'matching_lines': [['6\'. [...] x mu ta-ma-tu₂']]
    }


def test_update_lemmatization(transliterated_fragment):
    tokens = transliterated_fragment.text.lemmatization.to_list()
    tokens[1][1]['uniqueLemma'] = ['nu I']
    lemmatization = Lemmatization.from_list(tokens)
    expected = Fragment.from_dict({
        **transliterated_fragment.to_dict(),
        'lemmatization': tokens,
        'text': (transliterated_fragment
                 .text.update_lemmatization(lemmatization)
                 .to_dict())
    })

    assert transliterated_fragment.update_lemmatization(lemmatization) ==\
        expected


def test_update_lemmatization_incompatible(fragment):
    lemmatization = Lemmatization.from_list(
        [[{'value': 'mu', 'uniqueLemma': []}]]
    )
    with pytest.raises(LemmatizationError):
        fragment.update_lemmatization(lemmatization)


def test_filter_folios(user):
    wgl_folio = Folio('WGL', '1')
    folios = Folios((
        wgl_folio,
        Folio('XXX', '1')
    ))
    expected = Folios((
        wgl_folio,
    ))

    assert folios.filter(user) == expected


@pytest.mark.parametrize("old,new,type_", [
    ('', 'new', 'Transliteration'),
    ('old', 'new', 'Revision'),
])
@freeze_time("2018-09-07 15:41:24.032")
def test_add_record(old, new, type_, record, user):
    expected_entry = RecordEntry(
        user.ebl_name,
        type_,
        datetime.datetime.utcnow().isoformat()
    )
    assert record.add_entry(old, new, user) == Record((
        *record.entries,
        expected_entry
    ))


def test_set_references(fragment, reference):
    references = (reference,)
    updated_fragment = fragment.set_references(references)

    assert updated_fragment.references == references
