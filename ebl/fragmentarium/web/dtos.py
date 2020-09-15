import attr
from marshmallow import fields, pre_dump  # pyre-ignore

from ebl.fragmentarium.application.fragment_schema import FragmentSchema
from ebl.fragmentarium.domain.fragment import Fragment
from ebl.users.domain.user import User
from ebl.fragmentarium.domain.museum_number import MuseumNumber
from ebl.errors import DataError


class FragmentDtoSchema(FragmentSchema):
    atf = fields.Function(lambda fragment: fragment.text.atf)
    has_photo = fields.Function(
        lambda _, context: context["has_photo"], data_key="hasPhoto"
    )

    @pre_dump
    def filter_folios(self, data, **kwargs):
        return attr.evolve(data, folios=data.folios.filter(self.context["user"]))


def create_response_dto(fragment: Fragment, user: User, has_photo: bool):
    return FragmentDtoSchema(  # pyre-ignore[16,28]
        context={"user": user, "has_photo": has_photo}
    ).dump(fragment)


def parse_museum_number(number: str) -> MuseumNumber:
    try:
        return MuseumNumber.of(number)
    except ValueError as error:
        raise DataError(error)
