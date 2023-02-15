from marshmallow import fields, post_dump

from ebl.bibliography.application.reference_schema import ApiReferenceSchema
from ebl.errors import DataError
from ebl.fragmentarium.application.fragment_schema import FragmentSchema
from ebl.fragmentarium.domain.fragment import Fragment
from ebl.transliteration.domain.museum_number import MuseumNumber
from ebl.users.domain.user import User, Guest
from ebl.common.folios import HIDDEN_SCOPES


class FragmentDtoSchema(FragmentSchema):
    atf = fields.Function(lambda fragment: fragment.text.atf)
    has_photo = fields.Function(
        lambda _, context: context["has_photo"], data_key="hasPhoto"
    )
    references = fields.Nested(ApiReferenceSchema, many=True)

    class Meta:
        exclude = ("authorized_scopes",)

    @post_dump
    def exclude_hidden_folios(self, data, **kwargs):
        if "folios" in data:
            user = self.context.get("user", Guest())
            data["folios"] = [
                folio
                for folio in data["folios"]
                if user.has_scope(f"read:{folio['name']}-folios")
                or f"read:{folio['name']}-folios" not in HIDDEN_SCOPES
            ]
        return data


def create_response_dto(fragment: Fragment, user: User, has_photo: bool):
    return FragmentDtoSchema(context={"user": user, "has_photo": has_photo}).dump(
        fragment
    )


def parse_museum_number(number: str) -> MuseumNumber:
    try:
        return MuseumNumber.of(number)
    except ValueError as error:
        raise DataError(error) from error
