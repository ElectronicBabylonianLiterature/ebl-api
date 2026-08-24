from marshmallow import fields

from ebl.iiif.application.iiif_fields import LanguageMapField, OmitEmptyMixin
from ebl.iiif.application.iiif_resource_schemas import (
    AgentSchema,
    ExternalResourceSchema,
    ImageResourceSchema,
    MetadataEntrySchema,
    RequiredStatementSchema,
)


class PaintingAnnotationSchema(OmitEmptyMixin):
    id = fields.String(required=True)
    type = fields.String(required=True)
    motivation = fields.String(required=True)
    target = fields.String(required=True)
    body = fields.Nested(ImageResourceSchema, required=True)


class AnnotationPageSchema(OmitEmptyMixin):
    id = fields.String(required=True)
    type = fields.String(required=True)
    items = fields.List(fields.Nested(PaintingAnnotationSchema), required=True)


class CanvasSchema(OmitEmptyMixin):
    id = fields.String(required=True)
    type = fields.String(required=True)
    label = LanguageMapField()
    width = fields.Integer(required=True)
    height = fields.Integer(required=True)
    items = fields.List(fields.Nested(AnnotationPageSchema), required=True)
    thumbnail = fields.List(fields.Nested(ImageResourceSchema))
    rendering = fields.List(fields.Nested(ExternalResourceSchema))
    rights = fields.String()


class ManifestSchema(OmitEmptyMixin):
    context = fields.String(required=True, data_key="@context")
    id = fields.String(required=True)
    type = fields.String(required=True)
    label = LanguageMapField(required=True)
    summary = LanguageMapField()
    metadata = fields.List(fields.Nested(MetadataEntrySchema))
    required_statement = fields.Nested(
        RequiredStatementSchema, data_key="requiredStatement"
    )
    rights = fields.String()
    provider = fields.List(fields.Nested(AgentSchema))
    homepage = fields.List(fields.Nested(ExternalResourceSchema))
    see_also = fields.List(fields.Nested(ExternalResourceSchema), data_key="seeAlso")
    part_of = fields.List(fields.Nested(ExternalResourceSchema), data_key="partOf")
    thumbnail = fields.List(fields.Nested(ImageResourceSchema))
    behavior = fields.List(fields.String())
    viewing_direction = fields.String(data_key="viewingDirection")
    items = fields.List(fields.Nested(CanvasSchema), required=True)
