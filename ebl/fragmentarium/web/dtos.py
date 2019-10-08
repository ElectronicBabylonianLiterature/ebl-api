from marshmallow import fields, Schema

from ebl.fragmentarium.application.fragment_schema import FragmentSchema, \
    FolioSchema
from ebl.fragmentarium.domain.fragment import Fragment
from ebl.users.domain.user import User


class TextSchema(Schema):
    atf = fields.String(required=True)


class FragmentDtoSchema(FragmentSchema):
    folios = fields.Function(lambda fragment, context: FolioSchema(
        many=True
    ).dump(fragment.folios.filter(context['user']).entries))
    atf = fields.Pluck(TextSchema, 'atf', dump_only=True, attribute='text')


def create_response_dto(fragment: Fragment,
                        user: User,
                        has_photo):
    schema = FragmentDtoSchema(context={'user': user})
    return {
        **schema.dump(fragment),
        'has_photo': has_photo
    }
