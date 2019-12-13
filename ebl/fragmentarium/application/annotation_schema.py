from marshmallow import Schema, fields, post_load

from ebl.fragmentarium.domain.annotation import Geometry, AnnotationData, Annotation


class GeometrySchema(Schema):
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
