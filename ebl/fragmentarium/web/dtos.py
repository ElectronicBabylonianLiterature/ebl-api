from ebl.auth0 import User
from ebl.fragmentarium.domain.fragment import Fragment


def create_response_dto(fragment: Fragment, user: User):
    return {
        **fragment.to_dict_for(user),
        'atf': fragment.text.atf
    }
