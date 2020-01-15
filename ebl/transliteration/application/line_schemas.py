from typing import List, Mapping, Sequence, Tuple, Type

from marshmallow import Schema, fields, post_load

from ebl.transliteration.application.token_schemas import dump_tokens, load_tokens
from ebl.transliteration.domain.labels import LineNumberLabel
from ebl.transliteration.domain.line import (
    ControlLine,
    EmptyLine,
    Line,
    TextLine,
    LooseDollarLine,
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

    @post_load
    def make_line(self, data, **kwargs):
        return LooseDollarLine.of_single(data["content"][0].value)


_schemas: Mapping[str, Type[Schema]] = {
    "TextLine": TextLineSchema,
    "ControlLine": ControlLineSchema,
    "EmptyLine": EmptyLineSchema,
    "LooseDollarLine": LooseDollarLineSchema,
}


def dump_line(line: Line) -> dict:
    return _schemas[type(line).__name__]().dump(line)


def dump_lines(lines: Sequence[Line]) -> List[dict]:
    return list(map(dump_line, lines))


def load_line(data: dict) -> Line:
    return _schemas[data["type"]]().load(data)


def load_lines(lines: Sequence[dict]) -> Tuple[Line, ...]:
    return tuple(map(load_line, lines))
