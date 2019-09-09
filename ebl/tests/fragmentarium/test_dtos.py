from ebl.fragment.fragment_info import FragmentInfo
from ebl.fragmentarium.dtos import create_response_dto
from ebl.fragmentarium.fragment_search import FragmentInfoSchema


def test_create_response_dto(lemmatized_fragment, user):
    assert create_response_dto(lemmatized_fragment, user) == {
        **lemmatized_fragment.to_dict_for(user),
        'atf': lemmatized_fragment.text.atf
    }


def test_create_fragment_info_dto(lemmatized_fragment):
    line = '1. kur'
    info = FragmentInfo.of(lemmatized_fragment, ((line,),))
    assert FragmentInfoSchema().dump(info) == {
        'number': info.number,
        'accession': info.accession,
        'script': info.script,
        'description': info.description,
        'matchingLines': [[line]]
    }
