import attr
from marshmallow import fields, pre_dump  # pyre-ignore

from ebl.fragmentarium.application.fragment_schema import FragmentSchema
from ebl.fragmentarium.domain.fragment import Fragment
from ebl.users.domain.user import User


class FragmentDtoSchema(FragmentSchema):
    atf = fields.Function(lambda fragment: fragment.text.atf)
    has_photo = fields.Function(
        lambda _, context: context["has_photo"], data_key="hasPhoto"
    )

    @pre_dump
    def filter_folios(self, data, **kwargs):
        return attr.evolve(data, folios=data.folios.filter(self.context["user"]))


def create_response_dto(fragment: Fragment, user: User, has_photo: bool):
    return FragmentDtoSchema(context={"user": user, "has_photo": has_photo}).dump(
        fragment
    )
