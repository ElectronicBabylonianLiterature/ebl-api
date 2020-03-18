from functools import singledispatchmethod  # type: ignore
from typing import List, Mapping, Sequence, Tuple, Type, Union

from marshmallow import Schema, fields, post_load

from ebl.schemas import NameEnum
from ebl.transliteration.application.line_number_schemas import (
    dump_line_number,
    load_line_number,
)
from ebl.transliteration.application.note_line_part_schemas import (
    dump_parts,
    load_parts,
)
from ebl.transliteration.application.token_schemas import dump_tokens, load_tokens
from ebl.transliteration.domain import atf
from ebl.transliteration.domain.at_line import (
    SealAtLine,
    HeadingAtLine,
    ColumnAtLine,
    SurfaceAtLine,
    ObjectAtLine,
    DiscourseAtLine,
    DivisionAtLine,
    CompositeAtLine,
)
from ebl.transliteration.domain.dollar_line import (
    ImageDollarLine,
    LooseDollarLine,
    RulingDollarLine,
    ScopeContainer,
    StateDollarLine,
    SealDollarLine,
)
from ebl.transliteration.domain.labels import LineNumberLabel, ColumnLabel, SurfaceLabel
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
    line_number = fields.Function(
        lambda line: dump_line_number(line.line_number),
        load_line_number,
        missing=None,
        data_key="lineNumber",
    )

    @post_load
    def make_line(self, data, **kwargs):
        return TextLine.of_legacy_iterable(
            LineNumberLabel.from_atf(data["prefix"]),
            data["content"],
            data["line_number"],
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


class SealDollarLineSchema(LineSchema):
    type = fields.Constant("SealDollarLine", required=True)
    number = fields.Int(required=True)

    @post_load
    def make_line(self, data, **kwargs):
        return SealDollarLine(data["number"])


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


class SealAtLineSchema(LineSchema):
    type = fields.Constant("SealAtLine", required=True)
    number = fields.Int(required=True)

    @post_load
    def make_line(self, data, **kwargs):
        return SealAtLine(data["number"])


class HeadingAtLineSchema(LineSchema):
    type = fields.Constant("HeadingAtLine", required=True)
    number = fields.Int(required=True)

    @post_load
    def make_line(self, data, **kwargs):
        return HeadingAtLine(data["number"])


class LabelSchema(Schema):
    status = fields.List(NameEnum(atf.Status), required=True)


class ColumnLabelSchema(LabelSchema):
    column = fields.Int(required=True)

    @post_load
    def make_label(self, data, **kwargs):
        return ColumnLabel(data["status"], data["column"])


class SurfaceLabelSchema(LabelSchema):
    surface = NameEnum(atf.Surface, required=True)
    text = fields.String(default="")

    @post_load
    def make_label(self, data, **kwargs):
        return SurfaceLabel(data["status"], data["surface"], data["text"])


class ColumnAtLineSchema(LineSchema):
    type = fields.Constant("ColumnAtLine", required=True)
    column_label = fields.Nested(ColumnLabelSchema, required=True)

    @post_load
    def make_line(self, data, **kwargs):
        return ColumnAtLine(data["column_label"])


class DiscourseAtLineSchema(LineSchema):
    type = fields.Constant("DiscourseAtLine", required=True)
    discourse_label = NameEnum(atf.Discourse, required=True)

    @post_load
    def make_line(self, data, **kwargs):
        return DiscourseAtLine(data["discourse_label"])


class SurfaceAtLineSchema(LineSchema):
    type = fields.Constant("SurfaceAtLine", required=True)
    surface_label = fields.Nested(SurfaceLabelSchema, required=True)

    @post_load
    def make_line(self, data, **kwargs):
        return SurfaceAtLine(data["surface_label"])


class ObjectAtLineSchema(LineSchema):
    type = fields.Constant("ObjectAtLine", required=True)
    status = fields.List(NameEnum(atf.Status), required=True)
    object_label = NameEnum(atf.Object, required=True)
    text = fields.String(default="", required=True)

    @post_load
    def make_line(self, data, **kwargs):
        return ObjectAtLine(data["status"], data["object_label"], data["text"])


class DivisionAtLineSchema(LineSchema):
    type = fields.Constant("DivisionAtLine", required=True)
    text = fields.String(required=True)
    number = fields.Int(required=False, allow_none=True, default=None)

    @post_load
    def make_line(self, data, **kwargs):
        return DivisionAtLine(data["text"], data["number"])


class CompositeAtLineSchema(LineSchema):
    type = fields.Constant("CompositeAtLine", required=True)
    composite = NameEnum(atf.Composite, required=True)
    text = fields.String(required=True)
    number = fields.Int(required=False, allow_none=True, default=None)

    @post_load
    def make_line(self, data, **kwargs):
        return CompositeAtLine(data["composite"], data["text"], data["number"])


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
    "SealDollarLine": SealDollarLineSchema,
    "StateDollarLine": StateDollarLineSchema,
    "SealAtLine": SealAtLineSchema,
    "HeadingAtLine": HeadingAtLineSchema,
    "ColumnAtLine": ColumnAtLineSchema,
    "SurfaceAtLine": SurfaceAtLineSchema,
    "ObjectAtLine": ObjectAtLineSchema,
    "DiscourseAtLine": DiscourseAtLineSchema,
    "DivisionAtLine": DivisionAtLineSchema,
    "CompositeAtLine": CompositeAtLineSchema,
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
