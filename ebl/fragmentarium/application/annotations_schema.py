from marshmallow import Schema, fields, post_load  # pyre-ignore[21]

from ebl.fragmentarium.domain.annotation import (
    Geometry,
    AnnotationData,
    Annotation,
    Annotations,
)
from ebl.fragmentarium.domain.museum_number import MuseumNumber


class GeometrySchema(Schema):  # pyre-ignore[11]
    x = fields.Float(required=True)
    y = fields.Float(required=True)
    width = fields.Float(required=True)
    height = fields.Float(required=True)

    @post_load
    def make_geometry(self, data, **kwargs):
        return Geometry(**data)


class AnnotationDataSchema(Schema):
    id = fields.String(required=True)
    value = fields.String(required=True)
    path = fields.List(fields.Int, required=True)

    @post_load
    def make_data(self, data, **kwargs):
        return AnnotationData(**data)


class AnnotationSchema(Schema):
    geometry = fields.Nested(GeometrySchema(), required=True)
    data = fields.Nested(AnnotationDataSchema(), required=True)

    @post_load
    def make_annotation(self, data, **kwargs):
        return Annotation(**data)


class AnnotationsSchema(Schema):
    fragment_number = fields.String(required=True, data_key="fragmentNumber")
    annotations = fields.Nested(AnnotationSchema, many=True, required=True)

    @post_load
    def make_annotation(self, data, **kwargs):
        data["fragment_number"] = MuseumNumber.of(data["fragment_number"])
        return Annotations(**data)
