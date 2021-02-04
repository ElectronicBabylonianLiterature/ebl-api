from typing import Mapping, Type

from marshmallow import Schema  # pyre-ignore
from marshmallow_oneofschema import OneOfSchema  # pyre-ignore

from ebl.transliteration.application.at_line_schemas import (
    ColumnAtLineSchema,
    CompositeAtLineSchema,
    DiscourseAtLineSchema,
    DivisionAtLineSchema,
    HeadingAtLineSchema,
    ObjectAtLineSchema,
    SealAtLineSchema,
    SurfaceAtLineSchema,
)
from ebl.transliteration.application.dollar_line_schemas import (
    ImageDollarLineSchema,
    LooseDollarLineSchema,
    RulingDollarLineSchema,
    SealDollarLineSchema,
    StateDollarLineSchema,
)
from ebl.transliteration.application.line_schemas import (
    ControlLineSchema,
    EmptyLineSchema,
    NoteLineSchema,
    TextLineSchema,
)
from ebl.transliteration.application.parallel_line_schemas import (
    ParallelCompositionSchema,
    ParallelFragmentSchema,
    ParallelTextSchema,
)


PARALLEL_LINE_SCHEMAS: Mapping[str, Type[Schema]] = {  # pyre-ignore[11]
    "ParallelFragment": ParallelFragmentSchema,
    "ParallelText": ParallelTextSchema,
    "ParallelComposition": ParallelCompositionSchema,
}


class OneOfLineSchema(OneOfSchema):  # pyre-ignore[11]
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
        **PARALLEL_LINE_SCHEMAS,
    }


class ParallelLineSchema(OneOfSchema):
    type_field = "type"
    type_schemas = PARALLEL_LINE_SCHEMAS
