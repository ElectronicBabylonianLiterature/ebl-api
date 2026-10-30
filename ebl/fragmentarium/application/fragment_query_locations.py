from typing import Dict, Sequence, cast

from marshmallow import EXCLUDE, Schema, fields

from ebl.transliteration.application.one_of_line_schema import OneOfLineSchema
from ebl.transliteration.domain.at_line import (
    ColumnAtLine,
    ObjectAtLine,
    SealAtLine,
    SurfaceAtLine,
)
from ebl.transliteration.domain.line import Line
from ebl.transliteration.domain.line_label import LineLabel

LOCATION_LINE_TYPES = {"ColumnAtLine", "ObjectAtLine", "SealAtLine", "SurfaceAtLine"}


class FragmentQueryLineLocationSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    surface = fields.String(allow_none=True)
    column = fields.String(allow_none=True)
    object = fields.String(allow_none=True)
    seal_number = fields.Integer(allow_none=True, data_key="sealNumber")


def advance_location(current: LineLabel, line: Line) -> LineLabel:
    if isinstance(line, ColumnAtLine):
        return current.set_column(line.column_label)
    if isinstance(line, SurfaceAtLine):
        return current.set_surface(line.surface_label)
    if isinstance(line, ObjectAtLine):
        return current.set_object(line.label)
    if isinstance(line, SealAtLine):
        return current.set_seal(line.number)
    return current


def location_of(label: LineLabel) -> dict:
    return {
        "surface": label.surface.to_value() if label.surface else None,
        "column": label.column.to_value() if label.column else None,
        "object": label.object.to_value() if label.object else None,
        "sealNumber": label.seal_number,
    }


def locations_of_data(lines: Sequence[dict], indices: Sequence[int]) -> Dict[int, dict]:
    if not indices:
        return {}
    selected_indices = set(indices)
    last_index = max(selected_indices)
    current = LineLabel(None, None, None, None, None)
    locations: Dict[int, dict] = {}
    schema = OneOfLineSchema()
    for index, line in enumerate(lines):
        if index > last_index:
            break
        if line.get("type") in LOCATION_LINE_TYPES:
            current = advance_location(
                current, cast(Line, schema.load(line, unknown=EXCLUDE))
            )
        if index in selected_indices:
            locations[index] = location_of(current)
    return locations
