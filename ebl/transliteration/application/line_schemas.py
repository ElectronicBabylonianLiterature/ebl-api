from functools import singledispatchmethod  # type: ignore
from typing import List, Mapping, Sequence, Tuple, Type, Union

from marshmallow import Schema, fields, post_load

from ebl.schemas import NameEnum
from ebl.transliteration.application.note_line_part_schemas import (
    dump_parts,
    load_parts,
)
from ebl.transliteration.application.token_schemas import dump_tokens, load_tokens
from ebl.transliteration.domain import atf
from ebl.transliteration.domain.dollar_line import (
    ImageDollarLine,
    LooseDollarLine,
    RulingDollarLine,
    ScopeContainer,
    StateDollarLine,
)
from ebl.transliteration.domain.labels import LineNumberLabel
from ebl.transliteration.domain.line import (
    ControlLine,
    EmptyLine,
    Line,
)
from ebl.transliteration.domain.note_line import NoteLine
from ebl.transliteration.domain.text_line import TextLine


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
    status = NameEnum(atf.DollarStatus, missing=None)

    @post_load
    def make_line(self, data, **kwargs):
        return RulingDollarLine(data["number"], data["status"])


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
    type = fields.Constant("StateDollarLine", required=True, allow_none=True)
    qualification = NameEnum(atf.Qualification, required=True, allow_none=True)
    extent = fields.Function(
        lambda strict: StateDollarLineSchema.dump_extent(strict.extent),
        lambda value: value,
        required=True,
        allow_none=True,
    )
    scope = fields.Nested(ScopeContainerSchema, required=True, allow_none=True)
    state = NameEnum(atf.State, required=True, allow_none=True)
    status = NameEnum(atf.DollarStatus, required=True, allow_none=True)

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


class NoteLineSchema(LineSchema):
    type = fields.Constant("NoteLine", required=True)
    parts = fields.Function(
        lambda line: dump_parts(line.parts), load_parts, required=True
    )

    @post_load
    def make_line(self, data, **kwargs):
        return NoteLine(data["parts"])


_schemas: Mapping[str, Type[Schema]] = {
    "TextLine": TextLineSchema,
    "ControlLine": ControlLineSchema,
    "EmptyLine": EmptyLineSchema,
    "LooseDollarLine": LooseDollarLineSchema,
    "ImageDollarLine": ImageDollarLineSchema,
    "RulingDollarLine": RulingDollarLineSchema,
    "StateDollarLine": StateDollarLineSchema,
    "NoteLine": NoteLineSchema,
}


def dump_line(line: Line) -> dict:
    return _schemas[type(line).__name__]().dump(line)


def dump_lines(lines: Sequence[Line]) -> List[dict]:
    return list(map(dump_line, lines))


def load_line(data: dict) -> Line:
    return _schemas[data["type"]]().load(data)


def load_lines(lines: Sequence[dict]) -> Tuple[Line, ...]:
    return tuple(map(load_line, lines))
