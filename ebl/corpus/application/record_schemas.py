from marshmallow import (
    Schema,
    fields,
    post_load,
)

from ebl.corpus.domain.record import Author, AuthorRole, Record, Translator
from ebl.schemas import NameEnumField


class AuthorSchema(Schema):
    name = fields.String(required=True)
    prefix = fields.String(required=True)
    role = NameEnumField(AuthorRole, required=True)
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


class RecordSchema(Schema):
    authors = fields.Nested(AuthorSchema, many=True, required=True)
    translators = fields.Nested(TranslatorSchema, many=True, required=True)
    publication_date = fields.String(required=True, data_key="publicationDate")

    @post_load
    def make_record(self, data: dict, **kwargs) -> Record:
        return Record(
            tuple(data["authors"]), tuple(data["translators"]), data["publication_date"]
        )
