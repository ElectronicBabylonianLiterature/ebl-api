from marshmallow import Schema, fields

from ebl.iiif.application.iiif_fields import LanguageMapField, OmitEmptyMixin


class ImageServiceSchema(Schema):
    id = fields.String(required=True)
    type = fields.String(required=True)
    profile = fields.String(required=True)


class ImageResourceSchema(OmitEmptyMixin):
    id = fields.String(required=True)
    type = fields.String(required=True)
    format = fields.String(required=True)
    width = fields.Integer(required=True)
    height = fields.Integer(required=True)
    service = fields.List(fields.Nested(ImageServiceSchema))


class ExternalResourceSchema(OmitEmptyMixin):
    id = fields.String(required=True)
    type = fields.String(required=True)
    label = LanguageMapField()
    format = fields.String()


class AgentSchema(OmitEmptyMixin):
    id = fields.String(required=True)
    type = fields.String(required=True)
    label = LanguageMapField(required=True)
    homepage = fields.List(fields.Nested(ExternalResourceSchema))


class MetadataEntrySchema(Schema):
    label = LanguageMapField(required=True)
    value = LanguageMapField(required=True)


class RequiredStatementSchema(Schema):
    label = LanguageMapField(required=True)
    value = LanguageMapField(required=True)
