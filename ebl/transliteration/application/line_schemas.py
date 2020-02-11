from enum import Enum
from functools import singledispatch
from typing import List, Mapping, Sequence, Tuple, Type, Union

from marshmallow import Schema, fields, post_load

from ebl.schemas import NameEnum
from ebl.transliteration.application.token_schemas import dump_tokens, load_tokens
from ebl.transliteration.domain import atf
from ebl.transliteration.domain.labels import LineNumberLabel
from ebl.transliteration.domain.line import (
    ControlLine,
    EmptyLine,
    Line,
    TextLine,
    LooseDollarLine,
    ImageDollarLine,
    RulingDollarLine,
    StrictDollarLine,
    ScopeContainer,
)


class LineSchema(Schema):
    prefix = fields.String(required=True)
    content = fields.Function(
        lambda line: dump_tokens(line.content), load_tokens, required=True
    )


class TextLineSchema(LineSchema):
    type = fields.Constant("TextLine", required=True)

    @post_load
    def make_line(self, data, **kwargs):
        return TextLine.of_iterable(
            LineNumberLabel.from_atf(data["prefix"]), data["content"]
        )


class ControlLineSchema(LineSchema):
    type = fields.Constant("ControlLine", required=True)

    @post_load
    def make_line(self, data, **kwargs):
        return ControlLine(data["prefix"], data["content"])


class EmptyLineSchema(LineSchema):
    type = fields.Constant("EmptyLine", required=True)

    @post_load
    def make_line(self, data, **kwargs):
        return EmptyLine()


class LooseDollarLineSchema(LineSchema):
    type = fields.Constant("LooseDollarLine", required=True)
    text = fields.String(required=True)

    @post_load
    def make_line(self, data, **kwargs):
        return LooseDollarLine(data["text"])


class ImageDollarLineSchema(LineSchema):
    type = fields.Constant("ImageDollarLine", required=True)
    number = fields.String(required=True)
    letter = fields.String(required=True, allow_none=True)
    text = fields.String(required=True)

    @post_load
    def make_line(self, data, **kwargs):
        return ImageDollarLine(data["number"], data["letter"], data["text"])


class RulingDollarLineSchema(LineSchema):
    type = fields.Constant("RulingDollarLine", required=True)
    number = NameEnum(atf.Ruling, required=True)

    @post_load
    def make_line(self, data, **kwargs):
        return RulingDollarLine(data["number"])


class ScopeContainerSchema(Schema):
    type = fields.Function(
        lambda scope_container: type(scope_container.content).__name__,
        lambda value: value,
        required=True,
    )
    content = fields.Function(
        lambda scope_container: scope_container.content.name,
        lambda value: value,
        required=True,
    )
    text = fields.String(required=True)

    @post_load
    def make_line(self, data, **kwargs):
        return ScopeContainer(
            self.load_scope(data["type"], data["content"]), data["text"]
        )

    def load_scope(self, type: str, content: str):
        scope_types: Mapping[
            str, Union[Type[atf.Surface], Type[atf.Scope], Type[atf.Object]]
        ] = {"Surface": atf.Surface, "Scope": atf.Scope, "Object": atf.Object}
        return scope_types[type][content]


@singledispatch
def value_serialize(val):
    return str(val)


@value_serialize.register
def vs_enum(val: Enum):
    return val.name


def tuple_to_string(str_tuple: str):
    list_ = str_tuple[1:-1].split(",")
    return (int(list_[0]), int(list_[int(1)]))


class StrictDollarLineSchema(LineSchema):
    type = fields.Constant("StrictDollarLine", required=True)
    qualification = NameEnum(atf.Qualification, required=True, allow_none=True)
    extent = fields.Function(
        lambda obj: {
            "value": value_serialize(obj.extent),
            "type": type(obj.extent).__name__,
        },
        lambda obj: obj,
        required=True,
    )
    scope = fields.Nested(ScopeContainerSchema, required=True)
    state = NameEnum(atf.State, required=True, allow_none=True)
    status = NameEnum(atf.Status, required=True, allow_none=True)

    @post_load
    def make_line(self, data, **kwargs):
        return StrictDollarLine(
            data["qualification"],
            self.load_extent(data["extent"]["type"], data["extent"]["value"]),
            data["scope"],
            data["state"],
            data["status"],
        )

    def load_extent(self, type: str, extent: str):
        _extent: Mapping = {
            "Extent": lambda z: atf.Extent[z],
            "int": lambda z: int(z),
            "tuple": tuple_to_string,
        }
        return _extent[type](extent)


_schemas: Mapping[str, Type[Schema]] = {
    "TextLine": TextLineSchema,
    "ControlLine": ControlLineSchema,
    "EmptyLine": EmptyLineSchema,
    "LooseDollarLine": LooseDollarLineSchema,
    "ImageDollarLine": ImageDollarLineSchema,
    "RulingDollarLine": RulingDollarLineSchema,
    "StrictDollarLine": StrictDollarLineSchema,
}


def dump_line(line: Line) -> dict:
    return _schemas[type(line).__name__]().dump(line)


def dump_lines(lines: Sequence[Line]) -> List[dict]:
    return list(map(dump_line, lines))


def load_line(data: dict) -> Line:
    return _schemas[data["type"]]().load(data)


def load_lines(lines: Sequence[dict]) -> Tuple[Line, ...]:
    return tuple(map(load_line, lines))
