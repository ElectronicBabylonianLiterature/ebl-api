from ebl.fragment.fragment_info import FragmentInfo
from ebl.fragment.record import RecordType
from ebl.fragmentarium.dtos import create_response_dto
from ebl.fragmentarium.fragment_info_schema import FragmentInfoSchema
from ebl.tests.factories.fragment import LemmatizedFragmentFactory


def test_create_response_dto(user):
    lemmatized_fragment = LemmatizedFragmentFactory.build()
    assert create_response_dto(lemmatized_fragment, user) == {
        **lemmatized_fragment.to_dict_for(user),
        'atf': lemmatized_fragment.text.atf
    }


def test_create_fragment_info_dto():
    lemmatized_fragment = LemmatizedFragmentFactory.build()
    line = '1. kur'
    info = FragmentInfo.of(lemmatized_fragment, ((line,),))
    record_entry = lemmatized_fragment.record.entries[0]
    is_transliteration = record_entry.type == RecordType.TRANSLITERATION
    assert FragmentInfoSchema().dump(info) == {
        'number': info.number,
        'accession': info.accession,
        'script': info.script,
        'description': info.description,
        'matchingLines': [[line]],
        'editor': record_entry.user if is_transliteration else '',
        'editionDate': record_entry.date if is_transliteration else ''
    }
