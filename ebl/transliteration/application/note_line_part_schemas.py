from typing import List, Mapping, Sequence, Type

from marshmallow import Schema, fields, post_load

from ebl.schemas import NameEnum
from ebl.transliteration.domain.language import Language
from ebl.transliteration.domain.note_line import (
    EmphasisPart,
    LanguagePart,
    NotePart,
    StringPart,
)


class StringPartSchema(Schema):
    type = fields.Constant("StringPart", required=True)
    text = fields.String(required=True)

    @post_load
    def make_part(self, data, **kwargs):
        return StringPart(data["text"])


class EmphasisPartSchema(Schema):
    type = fields.Constant("EmphasisPart", required=True)
    text = fields.String(required=True)

    @post_load
    def make_part(self, data, **kwargs):
        return EmphasisPart(data["text"])


class LanguagePartSchema(Schema):
    type = fields.Constant("LangugeSchema", required=True)
    text = fields.String(required=True)
    language = NameEnum(Language, required=True)

    @post_load
    def make_part(self, data, **kwargs):
        return LanguagePart(data["text"], data["language"])


_schemas: Mapping[str, Type[Schema]] = {
    "StringPart": StringPartSchema,
    "EmphasisPart": EmphasisPartSchema,
    "LanguagePart": LanguagePartSchema,
}


def dump_part(part: NotePart) -> dict:
    return _schemas[type(part).__name__]().dump(part)


def dump_parts(parts: Sequence[NotePart]) -> List[dict]:
    return list(map(dump_part, parts))


def load_part(data: dict) -> NotePart:
    return _schemas[data["type"]]().load(data)


def load_parts(parts: Sequence[dict]) -> Sequence[NotePart]:
    return tuple(map(load_part, parts))
