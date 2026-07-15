import contextvars
from typing import Optional, Sequence
from marshmallow import fields

from ebl.bibliography.application.reference_schema import ApiReferenceSchema
from ebl.errors import DataError
from ebl.fragmentarium.application.fragment_schema import FragmentSchema
from ebl.fragmentarium.application.realia_info import RealiaInfoSchema
from ebl.fragmentarium.domain.archaeology import ExcavationNumber
from ebl.fragmentarium.domain.fragment import Fragment
from ebl.fragmentarium.domain.realia_info import RealiaInfo
from ebl.transliteration.domain.museum_number import MuseumNumber
from ebl.users.domain.user import User


fragment_user_context: contextvars.ContextVar = contextvars.ContextVar(
    "fragment_user", default=None
)
fragment_has_photo_context = contextvars.ContextVar("fragment_has_photo", default=False)
fragment_realia_info_context: contextvars.ContextVar = contextvars.ContextVar(
    "fragment_realia_info", default=None
)


def _dump_realia_info():
    realia_info = fragment_realia_info_context.get()
    return (
        None if realia_info is None else RealiaInfoSchema(many=True).dump(realia_info)
    )


class FragmentDtoSchema(FragmentSchema):
    atf = fields.Function(lambda fragment: fragment.text.atf)
    has_photo = fields.Function(
        lambda _: fragment_has_photo_context.get(), data_key="hasPhoto"
    )
    realia_info = fields.Function(lambda _: _dump_realia_info(), data_key="realiaInfo")
    references = fields.Nested(ApiReferenceSchema, many=True)


def create_response_dto(
    fragment: Fragment,
    user: User,
    has_photo: bool,
    realia_info: Optional[Sequence[RealiaInfo]] = None,
):
    fragment_user_context.set(user)
    fragment_has_photo_context.set(has_photo)
    fragment_realia_info_context.set(realia_info)
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
