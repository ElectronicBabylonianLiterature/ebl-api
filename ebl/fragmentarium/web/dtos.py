from ebl.fragmentarium.domain.fragment import Fragment
from ebl.fragmentarium.web.schema import FragmentSchema
from ebl.users.domain.user import User


def create_response_dto(fragment: Fragment,
                        user: User,
                        has_photo):
    schema = FragmentSchema()
    schema.context = {'user': user}
    return {
        **schema.dump(fragment),
        'has_photo': has_photo
    }
