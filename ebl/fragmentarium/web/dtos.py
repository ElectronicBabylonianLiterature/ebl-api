from ebl.fragmentarium.domain.fragment import Fragment
from ebl.users.domain.user import User


def create_response_dto(fragment: Fragment, user: User):
    return {
        **fragment.to_dict_for(user),
        'atf': fragment.text.atf
    }
