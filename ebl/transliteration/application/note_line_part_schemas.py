from typing import Mapping, Type

from marshmallow import Schema, fields, post_load  # pyre-ignore
from marshmallow_oneofschema import OneOfSchema  # pyre-ignore

from ebl.bibliography.application.reference_schema import ReferenceSchema
from ebl.schemas import NameEnum
from ebl.transliteration.application.token_schemas import OneOfTokenSchema
from ebl.transliteration.domain.language import Language
from ebl.transliteration.domain.note_line import (
    BibliographyPart,
    EmphasisPart,
    LanguagePart,
    StringPart,
)


class StringPartSchema(Schema):  # pyre-ignore[11]
    text = fields.String(required=True)

    @post_load  # pyre-ignore[56]
    def make_part(self, data, **kwargs) -> StringPart:
        return StringPart(data["text"])


class EmphasisPartSchema(Schema):
    text = fields.String(required=True)

    @post_load  # pyre-ignore[56]
    def make_part(self, data, **kwargs) -> EmphasisPart:
        return EmphasisPart(data["text"])


class LanguagePartSchema(Schema):
    language = NameEnum(Language, required=True)
    tokens = fields.Nested(OneOfTokenSchema, many=True, missing=None)

    @post_load  # pyre-ignore[56]
    def make_part(self, data, **kwargs) -> LanguagePart:
        return LanguagePart.of_transliteration(data["language"], data["tokens"])


class BibliographyPartSchema(Schema):
    reference = fields.Nested(ReferenceSchema, required=True)

    @post_load  # pyre-ignore[56]
    def make_part(self, data, **kwargs) -> BibliographyPart:
        return BibliographyPart(data["reference"])


class OneOfNoteLinePartSchema(OneOfSchema):  # pyre-ignore[11]
    type_field = "type"
    type_schemas: Mapping[str, Type[Schema]] = {
        "StringPart": StringPartSchema,
        "EmphasisPart": EmphasisPartSchema,
        "LanguagePart": LanguagePartSchema,
        "BibliographyPart": BibliographyPartSchema,
    }
