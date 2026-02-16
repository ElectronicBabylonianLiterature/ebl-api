import contextvars
from marshmallow import fields

from ebl.bibliography.application.reference_schema import ApiReferenceSchema
from ebl.errors import DataError
from ebl.fragmentarium.application.fragment_schema import FragmentSchema
from ebl.fragmentarium.domain.archaeology import ExcavationNumber
from ebl.fragmentarium.domain.fragment import Fragment
from ebl.transliteration.domain.museum_number import MuseumNumber
from ebl.users.domain.user import User


fragment_user_context = contextvars.ContextVar("fragment_user", default=None)
fragment_has_photo_context = contextvars.ContextVar("fragment_has_photo", default=False)


class FragmentDtoSchema(FragmentSchema):
    atf = fields.Function(lambda fragment: fragment.text.atf)
    has_photo = fields.Function(
        lambda _: fragment_has_photo_context.get(), data_key="hasPhoto"
    )
    references = fields.Nested(ApiReferenceSchema, many=True)


def create_response_dto(fragment: Fragment, user: User, has_photo: bool):
    fragment_user_context.set(user)
    fragment_has_photo_context.set(has_photo)
    return FragmentDtoSchema().dump(fragment)


def parse_museum_number(number: str) -> MuseumNumber:
    try:
        return MuseumNumber.of(number)
    except ValueError as error:
        raise DataError(error) from error


def parse_excavation_number(number: str) -> ExcavationNumber:
    try:
        return ExcavationNumber.of(number)
    except ValueError as error:
        raise DataError(error) from error
