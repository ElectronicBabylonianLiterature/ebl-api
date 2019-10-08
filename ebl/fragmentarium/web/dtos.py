import attr
from marshmallow import fields, pre_dump

from ebl.fragmentarium.application.fragment_schema import FragmentSchema
from ebl.fragmentarium.domain.fragment import Fragment
from ebl.users.domain.user import User


class FragmentDtoSchema(FragmentSchema):
    atf = fields.Function(lambda fragment: fragment.text.atf)

    @pre_dump
    def filter_folios(self, data, **kwargs):
        return attr.evolve(
            data,
            folios=data.folios.filter(self.context['user'])
        )


def create_response_dto(fragment: Fragment,
                        user: User,
                        has_photo):
    schema = FragmentDtoSchema(context={'user': user})
    return {
        **schema.dump(fragment),
        'has_photo': has_photo
    }
