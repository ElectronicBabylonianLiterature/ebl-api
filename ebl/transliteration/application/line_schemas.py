from enum import Enum
from functools import singledispatchmethod  # type: ignore
from typing import List, Mapping, Sequence, Tuple, Type, Union

from marshmallow import Schema, fields, post_load

from ebl.schemas import NameEnum
from ebl.transliteration.application.token_schemas import dump_tokens, load_tokens
from ebl.transliteration.domain import atf
from ebl.transliteration.domain.at_line import Seal, Column, Heading, AtLine
from ebl.transliteration.domain.labels import LineNumberLabel
from ebl.transliteration.domain.line import (
    ControlLine,
    EmptyLine,
    Line,
    TextLine,
)
from ebl.transliteration.domain.dollar_line import (
    LooseDollarLine,
    ImageDollarLine,
    RulingDollarLine,
    ScopeContainer,
    StateDollarLine,
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


class StateDollarLineSchema(LineSchema):
    type = fields.Constant("StateDollarLine", required=True)
    qualification = NameEnum(atf.Qualification, required=True, allow_none=True)
    extent = fields.Function(
        lambda strict: StateDollarLineSchema.dump_extent(strict.extent),
        lambda value: value,
        required=True,
    )
    scope = fields.Nested(ScopeContainerSchema, required=True)
    state = NameEnum(atf.State, required=True, allow_none=True)
    status = NameEnum(atf.Status, required=True, allow_none=True)

    @post_load
    def make_line(self, data, **kwargs):
        return StateDollarLine(
            data["qualification"],
            StateDollarLineSchema.load_extent(data["extent"]),
            data["scope"],
            data["state"],
            data["status"],
        )

    @singledispatchmethod
    @staticmethod
    def load_extent(extent):
        return extent

    @load_extent.register(str)
    @staticmethod
    def load_extent_to_enum(extent: str):
        return atf.Extent[extent]

    @singledispatchmethod
    @staticmethod
    def dump_extent(extent):
        return extent

    @dump_extent.register(atf.Extent)
    @staticmethod
    def dump_extent_to_str(extent: atf.Extent):
        return extent.name


class AtLineSchema(LineSchema):
    type = fields.Constant("AtLine", required=True)
    structural_tag_type = fields.Function(
        lambda at_line: type(at_line.structural_tag).__name__, lambda at_line: at_line
    )
    structural_tag = fields.Function(
        lambda at_line: AtLineSchema.dump_extent(at_line.structural_tag),
        lambda at_line: at_line,
    )
    status = NameEnum(atf.Status, required=False, allow_none=True)
    text = fields.String(required=False)

    @post_load
    def make_line(self, data, **kwargs):
        return AtLine(
            self.load_extent(data["structural_tag_type"], data["structural_tag"]),
            data["status"],
            data["text"],
        )

    @singledispatchmethod
    @staticmethod
    def dump_extent(number: Union[Type[Seal], Type[Heading], Type[Column]]):
        return number.number

    @dump_extent.register(Enum)
    @staticmethod
    def dump_extent_to_enum(enum: Enum):
        return enum.name

    def load_extent(self, structural_tag_type: str, structural_tag: str):
        structural_tag_types: Mapping[
            str,
            Union[
                Type[atf.Surface],
                Type[atf.Object],
                Seal,
                Column,
                Heading,
                atf.Discourse,
            ],
        ] = {
            "Surface": atf.Surface,
            "Object": atf.Object,
            "Seal": Seal,
            "Column": Column,
            "Heading": Heading,
            "Discourse": atf.Discourse,
        }
        return AtLineSchema.load_object(
            structural_tag, structural_tag_types[structural_tag_type]
        )

    @singledispatchmethod
    @staticmethod
    def load_object(structural_tag: int, structural_tag_type):
        return structural_tag_type(structural_tag)

    @load_object.register(str)
    @staticmethod
    def load_object_to_enum(structural_tag: str, structural_tag_type):
        return structural_tag_type[structural_tag]


_schemas: Mapping[str, Type[Schema]] = {
    "TextLine": TextLineSchema,
    "ControlLine": ControlLineSchema,
    "EmptyLine": EmptyLineSchema,
    "LooseDollarLine": LooseDollarLineSchema,
    "ImageDollarLine": ImageDollarLineSchema,
    "RulingDollarLine": RulingDollarLineSchema,
    "StateDollarLine": StateDollarLineSchema,
    "AtLine": AtLineSchema,
}


def dump_line(line: Line) -> dict:
    return _schemas[type(line).__name__]().dump(line)


def dump_lines(lines: Sequence[Line]) -> List[dict]:
    return list(map(dump_line, lines))


def load_line(data: dict) -> Line:
    return _schemas[data["type"]]().load(data)


def load_lines(lines: Sequence[dict]) -> Tuple[Line, ...]:
    return tuple(map(load_line, lines))
