from typing import Mapping, Type

from marshmallow import Schema, fields, post_load
from marshmallow_oneofschema import OneOfSchema

from ebl.bibliography.application.reference_schema import ReferenceSchema
from ebl.schemas import NameEnumField
from ebl.transliteration.application.token_schemas import OneOfTokenSchema
from ebl.transliteration.domain.language import Language
from ebl.transliteration.domain.markup import (
    BibliographyPart,
    BoldPart,
    EmphasisPart,
    LanguagePart,
    ParagraphPart,
    StringPart,
    SubscriptPart,
    SuperscriptPart,
    UrlPart,
)


class StringPartSchema(Schema):
    text = fields.String(required=True)

    @post_load
    def make_part(self, data, **kwargs) -> StringPart:
        return StringPart(data["text"])


class EmphasisPartSchema(Schema):
    text = fields.String(required=True)

    @post_load
    def make_part(self, data, **kwargs) -> EmphasisPart:
        return EmphasisPart(data["text"])


class SuperscriptPartSchema(Schema):
    text = fields.String(required=True)

    @post_load
    def make_part(self, data, **kwargs) -> SuperscriptPart:
        return SuperscriptPart(data["text"])


class SubscriptPartSchema(Schema):
    text = fields.String(required=True)

    @post_load
    def make_part(self, data, **kwargs) -> SubscriptPart:
        return SubscriptPart(data["text"])


class BoldPartSchema(Schema):
    text = fields.String(required=True)

    @post_load
    def make_part(self, data, **kwargs) -> BoldPart:
        return BoldPart(data["text"])


class LanguagePartSchema(Schema):
    language = NameEnumField(Language, required=True)
    tokens = fields.Nested(OneOfTokenSchema, many=True, load_default=None)

    @post_load
    def make_part(self, data, **kwargs) -> LanguagePart:
        return LanguagePart.of_transliteration(data["language"], data["tokens"])


class BibliographyPartSchema(Schema):
    reference = fields.Nested(ReferenceSchema, required=True)

    @post_load
    def make_part(self, data, **kwargs) -> BibliographyPart:
        return BibliographyPart(data["reference"])


class ParagraphPartSchema(Schema):
    @post_load
    def make_part(self, data, **kwargs) -> ParagraphPart:
        return ParagraphPart()


class UrlPartSchema(Schema):
    url = fields.String(required=True)
    text = fields.String(load_default="")

    @post_load
    def make_part(self, data, **kwargs) -> UrlPart:
        return UrlPart(**data)


class OneOfNoteLinePartSchema(OneOfSchema):
    type_field = "type"
    type_schemas: Mapping[str, Type[Schema]] = {
        "StringPart": StringPartSchema,
        "EmphasisPart": EmphasisPartSchema,
        "SuperscriptPart": SuperscriptPartSchema,
        "SubscriptPart": SubscriptPartSchema,
        "BoldPart": BoldPartSchema,
        "LanguagePart": LanguagePartSchema,
        "BibliographyPart": BibliographyPartSchema,
        "ParagraphPart": ParagraphPartSchema,
        "UrlPart": UrlPartSchema,
    }
