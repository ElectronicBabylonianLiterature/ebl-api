from ebl.fragmentarium.dtos import create_response_dto


def test_create_response_dto(lemmatized_fragment, user):
    assert create_response_dto(lemmatized_fragment, user) == {
        **lemmatized_fragment.to_dict_for(user),
        'atf': lemmatized_fragment.text.atf
    }
