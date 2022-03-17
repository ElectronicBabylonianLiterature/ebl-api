import attr
from marshmallow import fields, pre_dump

from ebl.bibliography.application.reference_schema import ApiReferenceSchema
from ebl.errors import DataError
from ebl.fragmentarium.application.fragment_schema import FragmentSchema
from ebl.fragmentarium.domain.fragment import Fragment
from ebl.fragmentarium.domain.museum_number import MuseumNumber
from ebl.transliteration.domain.parallel_line import ParallelFragment
from ebl.users.domain.user import User


class FragmentDtoSchema(FragmentSchema):
    atf = fields.Function(lambda fragment: fragment.text.atf)
    has_photo = fields.Function(
        lambda _, context: context["has_photo"], data_key="hasPhoto"
    )
    references = fields.Nested(ApiReferenceSchema, many=True)

    @pre_dump
    def filter_folios(self, data, **kwargs):
        return attr.evolve(data, folios=data.folios.filter(self.context["user"]))


def create_response_dto(fragment: Fragment, user: User, has_photo: bool):
    dto = FragmentDtoSchema(context={"user": user, "has_photo": has_photo}).dump(
        fragment
    )

    for line in dto["text"]["lines"]:
        if line["type"] == ParallelFragment.__name__:
            line["exists"] = False

    return dto


def parse_museum_number(number: str) -> MuseumNumber:
    try:
        return MuseumNumber.of(number)
    except ValueError as error:
        raise DataError(error) from error
