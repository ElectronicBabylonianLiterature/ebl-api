import datetime
from freezegun import freeze_time
import pytest
from ebl.fragmentarium.fragment import Fragment
from ebl.fragmentarium.fragment import Record
from ebl.fragmentarium.fragment import Folios
from ebl.fragmentarium.lemmatization import Lemmatization, LemmatizationError
from ebl.fragmentarium.transliteration import Transliteration
from ebl.fragmentarium.transliteration_query import TransliterationQuery


def test_to_dict(fragment):
    new_fragment = Fragment.from_dict(fragment.to_dict())

    assert new_fragment.to_dict() == fragment.to_dict()


def test_from_dict(fragment):
    new_fragment = Fragment.from_dict(fragment.to_dict())

    assert new_fragment == fragment


def test_to_dict_for(fragment, user):
    assert fragment.to_dict_for(user) == {
        **fragment.to_dict(),
        'folios': fragment.folios.filter(user).entries
    }


def test_equality(fragment, transliterated_fragment):
    new_fragment = Fragment.from_dict(fragment.to_dict())

    assert new_fragment == fragment
    assert new_fragment != transliterated_fragment


def test_accession(fragment):
    data = fragment.to_dict()
    new_fragment = Fragment.from_dict(data)

    assert new_fragment.accession == data['accession']


def test_cdli_number(fragment):
    data = fragment.to_dict()
    new_fragment = Fragment.from_dict(data)

    assert new_fragment.cdli_number == data['cdliNumber']


def test_bm_id_number(fragment):
    data = fragment.to_dict()
    new_fragment = Fragment.from_dict(data)

    assert new_fragment.bm_id_number == data['bmIdNumber']


def test_publication(fragment):
    data = fragment.to_dict()
    new_fragment = Fragment.from_dict(data)

    assert new_fragment.publication == data['publication']


def test_description(fragment):
    data = fragment.to_dict()
    new_fragment = Fragment.from_dict(data)

    assert new_fragment.description == data['description']


def test_collection(fragment):
    data = fragment.to_dict()
    new_fragment = Fragment.from_dict(data)

    assert new_fragment.collection == data['collection']


def test_script(fragment):
    data = fragment.to_dict()
    new_fragment = Fragment.from_dict(data)

    assert new_fragment.script == data['script']


def test_museum(fragment):
    data = fragment.to_dict()
    new_fragment = Fragment.from_dict(data)

    assert new_fragment.museum == data['museum']


def test_length(fragment):
    data = fragment.to_dict()
    new_fragment = Fragment.from_dict(data)

    assert new_fragment.length == fragment.length


def test_width(fragment):
    data = fragment.to_dict()
    new_fragment = Fragment.from_dict(data)

    assert new_fragment.width == fragment.width


def test_thickness(fragment):
    data = fragment.to_dict()
    new_fragment = Fragment.from_dict(data)

    assert new_fragment.thickness == fragment.thickness


def test_joins(fragment):
    data = fragment.to_dict()
    new_fragment = Fragment.from_dict(data)

    assert new_fragment.joins == fragment.joins


def test_transliteration(transliterated_fragment):
    data = transliterated_fragment.to_dict()
    new_fragment = Fragment.from_dict(data)

    assert new_fragment.transliteration == Transliteration(
        Lemmatization(data['lemmatization']).atf,
        data['notes'],
        data['signs']
    )


def test_record(transliterated_fragment):
    data = transliterated_fragment.to_dict()
    new_fragment = Fragment.from_dict(data)

    assert new_fragment.record == Record(data['record'])


def test_folios(fragment):
    data = fragment.to_dict()
    new_fragment = Fragment.from_dict(data)

    assert new_fragment.folios == Folios(data['folios'])


def test_lemmatization(fragment):
    tokens = [[{'value': '1.', 'uniqueLemma': []}]]
    data = {
        **fragment.to_dict(),
        'lemmatization': tokens
    }
    assert Fragment.from_dict(data).lemmatization == Lemmatization(tokens)


def test_hits(fragment):
    data = fragment.to_dict()
    new_fragment = Fragment.from_dict(data)

    assert new_fragment.hits == data.get('hits')


@freeze_time("2018-09-07 15:41:24.032")
def test_add_transliteration(fragment, user):
    transliteration = Transliteration('x x', fragment.transliteration.notes)
    lemmatization = Lemmatization.of_transliteration(transliteration)

    updated_fragment = fragment.update_transliteration(
        transliteration,
        user
    )
    expected_fragment = Fragment.from_dict({
        **fragment.to_dict(),
        'lemmatization': lemmatization.tokens,
        'record': [{
            'user': user.ebl_name,
            'type': 'Transliteration',
            'date': datetime.datetime.utcnow().isoformat()
        }]
    })

    assert updated_fragment == expected_fragment


@freeze_time("2018-09-07 15:41:24.032")
def test_update_transliteration(lemmatized_fragment, user):
    lines = lemmatized_fragment.transliteration.atf.split('\n')
    lines[1] = '2\'. [...] GI₆ mu u₄-š[u ...]'
    transliteration =\
        Transliteration('\n'.join(lines), 'updated notes', 'X X\nX')
    updated_fragment = lemmatized_fragment.update_transliteration(
        transliteration,
        user
    )
    lemmatization = lemmatized_fragment.lemmatization.merge(transliteration)

    expected_fragment = Fragment.from_dict({
        **lemmatized_fragment.to_dict(),
        'lemmatization': lemmatization.tokens,
        'notes': transliteration.notes,
        'signs': transliteration.signs,
        'record': [
            *lemmatized_fragment.record.entries,
            {
                'user': user.ebl_name,
                'type': 'Revision',
                'date': datetime.datetime.utcnow().isoformat()
            }
        ]
    })

    assert updated_fragment == expected_fragment


def test_update_notes(fragment, user):
    transliteration =\
        Transliteration(fragment.transliteration.atf, 'new notes')
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
    tokens = transliterated_fragment.lemmatization.tokens
    tokens[0][1]['uniqueLemma'] = ['nu I']
    expected = Fragment.from_dict({
        **transliterated_fragment.to_dict(),
        'lemmatization': tokens
    })
    lemmatization = Lemmatization(tokens)
    assert transliterated_fragment.update_lemmatization(lemmatization) ==\
        expected


def test_update_lemmatization_incompatible(fragment):
    lemmatization = Lemmatization([[{'value': '1.', 'uniqueLemma': []}]])
    with pytest.raises(LemmatizationError):
        fragment.update_lemmatization(lemmatization)


def test_filter_folios(user):
    wgl_folio = {
        'name': 'WGL',
        'number': '1'
    }
    folios = Folios([
        wgl_folio,
        {
            'name': 'XXX',
            'number': '1'
        },
    ])
    expected = Folios([
        wgl_folio
    ])

    assert folios.filter(user) == expected
