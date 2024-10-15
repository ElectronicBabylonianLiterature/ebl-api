from marshmallow import fields

from ebl.bibliography.application.reference_schema import ApiReferenceSchema
from ebl.errors import DataError
from ebl.fragmentarium.application.fragment_schema import FragmentSchema
from ebl.fragmentarium.domain.fragment import Fragment
from ebl.transliteration.domain.museum_number import MuseumNumber
from ebl.users.domain.user import User


class FragmentDtoSchema(FragmentSchema):
    atf = fields.Function(lambda fragment: fragment.text.atf)
    has_photo = fields.Function(
        lambda _, context: context["has_photo"], data_key="hasPhoto"
    )
    references = fields.Nested(ApiReferenceSchema, many=True)


def create_response_dto(fragment: Fragment, user: User, has_photo: bool):
    return FragmentDtoSchema(context={"user": user, "has_photo": has_photo}).dump(
        fragment
    )


def parse_museum_number(number: str) -> MuseumNumber:
    try:
        return MuseumNumber.of(number)
    except ValueError as error:
        raise DataError(error) from error
