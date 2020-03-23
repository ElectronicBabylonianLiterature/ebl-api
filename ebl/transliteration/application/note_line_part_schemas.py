from typing import Mapping, Type

from marshmallow import Schema, fields, post_load
from marshmallow_oneofschema import OneOfSchema

from ebl.schemas import NameEnum
from ebl.transliteration.domain.language import Language
from ebl.transliteration.domain.note_line import (
    EmphasisPart,
    LanguagePart,
    StringPart,
)


class StringPartSchema(Schema):
    text = fields.String(required=True)

    @post_load
    def make_part(self, data, **kwargs):
        return StringPart(data["text"])


class EmphasisPartSchema(Schema):
    text = fields.String(required=True)

    @post_load
    def make_part(self, data, **kwargs):
        return EmphasisPart(data["text"])


class LanguagePartSchema(Schema):
    text = fields.String(required=True)
    language = NameEnum(Language, required=True)

    @post_load
    def make_part(self, data, **kwargs):
        return LanguagePart(data["text"], data["language"])


class OneOfNoteLinePartSchema(OneOfSchema):
    type_field = "type"
    type_schemas: Mapping[str, Type[Schema]] = {
        "StringPart": StringPartSchema,
        "EmphasisPart": EmphasisPartSchema,
        "LanguagePart": LanguagePartSchema,
    }
