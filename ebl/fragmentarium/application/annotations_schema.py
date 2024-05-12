from marshmallow import Schema, fields, post_load, post_dump
import pydash
from ebl.fragmentarium.application.cropped_sign_image import CroppedSignSchema
from ebl.fragmentarium.application.fragment_schema import ScriptSchema
from ebl.fragmentarium.domain.annotation import (
    Geometry,
    AnnotationData,
    Annotation,
    Annotations,
    AnnotationValueType,
)
from ebl.fragmentarium.domain.fragment import Script
from ebl.transliteration.domain.museum_number import MuseumNumber
from ebl.schemas import ValueEnumField


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
    type = ValueEnumField(
        AnnotationValueType, load_default=AnnotationValueType.HAS_SIGN
    )
    sign_name = fields.String(load_default="", data_key="signName")
    value = fields.String(required=True)
    path = fields.List(fields.Int, required=True)

    @post_load
    def make_data(self, data, **kwargs):
        return AnnotationData(**data)


class AnnotationSchema(Schema):
    geometry = fields.Nested(GeometrySchema(), required=True)
    data = fields.Nested(AnnotationDataSchema(), required=True)
    cropped_sign = fields.Nested(
        CroppedSignSchema(), load_default=None, data_key="croppedSign"
    )

    @post_load
    def make_annotation(self, data, **kwargs):
        return Annotation(**data)

    @post_dump
    def filter_none(self, data, **kwargs):
        return pydash.omit_by(data, pydash.is_none)


class AnnotationsSchema(Schema):
    fragment_number = fields.String(required=True, data_key="fragmentNumber")
    provenance = fields.String(required=False, load_default=None)
    annotations = fields.List(fields.Nested(AnnotationSchema(), required=True))

    @post_load
    def make_annotation(self, data, **kwargs):
        data["fragment_number"] = MuseumNumber.of(data["fragment_number"])
        return Annotations(**data)

    @post_dump
    def filter_none(self, data, **kwargs):
        return pydash.omit_by(data, pydash.is_none)


class AnnotationsWithScriptSchema(AnnotationsSchema):
    script = fields.Nested(ScriptSchema(), load_default=Script())
