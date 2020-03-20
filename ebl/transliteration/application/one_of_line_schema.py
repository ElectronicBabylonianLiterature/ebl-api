from typing import Mapping, Type

from marshmallow import Schema
from marshmallow_oneofschema import OneOfSchema

from ebl.transliteration.application.at_line_schemas import (
    SealAtLineSchema,
    HeadingAtLineSchema,
    ColumnAtLineSchema,
    SurfaceAtLineSchema,
    ObjectAtLineSchema,
    DiscourseAtLineSchema,
    DivisionAtLineSchema,
    CompositeAtLineSchema,
)
from ebl.transliteration.application.dollar_line_schemas import (
    LooseDollarLineSchema,
    ImageDollarLineSchema,
    RulingDollarLineSchema,
    SealDollarLineSchema,
    StateDollarLineSchema,
)
from ebl.transliteration.application.line_schemas import (
    TextLineSchema,
    ControlLineSchema,
    EmptyLineSchema,
    NoteLineSchema,
)


class OneOfLineSchema(OneOfSchema):
    type_field = "type"
    type_schemas: Mapping[str, Type[Schema]] = {
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
