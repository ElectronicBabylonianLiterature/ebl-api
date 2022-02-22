from marshmallow import (
    Schema,
    fields,
    post_load,
)

from ebl.corpus.domain.record import Author, AuthorRole, Translator
from ebl.schemas import NameEnum


class AuthorSchema(Schema):
    name = fields.String(required=True)
    prefix = fields.String(required=True)
    role = NameEnum(AuthorRole, required=True)
    orcid_number = fields.String(required=True, data_key="orcidNumber")

    @post_load
    def make_author(self, data: dict, **kwargs) -> Author:
        return Author(data["name"], data["prefix"], data["role"], data["orcid_number"])


class TranslatorSchema(Schema):
    name = fields.String(required=True)
    prefix = fields.String(required=True)
    orcid_number = fields.String(required=True, data_key="orcidNumber")
    language = fields.String(required=True)

    @post_load
    def make_translator(self, data: dict, **kwargs) -> Translator:
        return Translator(
            data["name"], data["prefix"], data["orcid_number"], data["language"]
        )
