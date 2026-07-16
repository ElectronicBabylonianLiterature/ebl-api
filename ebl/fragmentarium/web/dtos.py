import contextvars
from typing import Sequence, cast
from marshmallow import fields

from ebl.bibliography.application.reference_schema import ApiReferenceSchema
from ebl.errors import DataError
from ebl.fragmentarium.application.fragment_schema import FragmentSchema
from ebl.fragmentarium.application.realia_info import (
    RealiaInfoSchema,
    resolve_realia_info,
)
from ebl.fragmentarium.domain.archaeology import ExcavationNumber
from ebl.fragmentarium.domain.fragment import Fragment
from ebl.fragmentarium.domain.realia_info import RealiaInfo
from ebl.realia.application.realia_repository import RealiaRepository
from ebl.transliteration.domain.museum_number import MuseumNumber
from ebl.users.domain.user import User


fragment_user_context: contextvars.ContextVar = contextvars.ContextVar(
    "fragment_user", default=None
)
fragment_has_photo_context = contextvars.ContextVar("fragment_has_photo", default=False)
fragment_realia_info_context: contextvars.ContextVar = contextvars.ContextVar(
    "fragment_realia_info", default=()
)


class FragmentDtoSchema(FragmentSchema):
    atf = fields.Function(lambda fragment: fragment.text.atf)
    has_photo = fields.Function(
        lambda _: fragment_has_photo_context.get(), data_key="hasPhoto"
    )
    realia_info = fields.Function(
        lambda _: RealiaInfoSchema(many=True).dump(fragment_realia_info_context.get()),
        data_key="realiaInfo",
    )
    references = fields.Nested(ApiReferenceSchema, many=True)


def create_response_dto(
    fragment: Fragment,
    user: User,
    has_photo: bool,
    realia_info: Sequence[RealiaInfo],
) -> dict:
    fragment_user_context.set(user)
    fragment_has_photo_context.set(has_photo)
    fragment_realia_info_context.set(realia_info)
    return cast(dict, FragmentDtoSchema().dump(fragment))


class FragmentDtoFactory:
    def __init__(self, realia_repository: RealiaRepository) -> None:
        self._realia_repository = realia_repository

    def create(self, fragment: Fragment, user: User, has_photo: bool) -> dict:
        return create_response_dto(
            fragment,
            user,
            has_photo,
            resolve_realia_info(fragment, self._realia_repository),
        )


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
