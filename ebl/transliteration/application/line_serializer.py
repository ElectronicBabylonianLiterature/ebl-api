from typing import List, Mapping, Sequence, Tuple, Type

from marshmallow import Schema

from ebl.transliteration.application.line_schemas import (
    TextLineSchema,
    ControlLineSchema,
    EmptyLineSchema,
    LooseDollarLineSchema,
    ImageDollarLineSchema,
    RulingDollarLineSchema,
    SealDollarLineSchema,
    StateDollarLineSchema,
    SealAtLineSchema,
    HeadingAtLineSchema,
    ColumnAtLineSchema,
    SurfaceAtLineSchema,
    ObjectAtLineSchema,
    DiscourseAtLineSchema,
    DivisionAtLineSchema,
    CompositeAtLineSchema,
    NoteLineSchema
)
from ebl.transliteration.domain.line import Line


_SCHEMAS: Mapping[str, Type[Schema]] = {
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
    return _SCHEMAS[type(line).__name__]().dump(line)


def dump_lines(lines: Sequence[Line]) -> List[dict]:
    return list(map(dump_line, lines))


def load_line(data: dict) -> Line:
    return _SCHEMAS[data["type"]]().load(data)


def load_lines(lines: Sequence[dict]) -> Tuple[Line, ...]:
    return tuple(map(load_line, lines))
