from marshmallow import fields, Schema


class CroppedAnnotationSchema(Schema):
    image = fields.String(required=True)
    fragment_number = fields.String(required=True, data_key="fragmentNumber")
    script = fields.String(required=True)
    label = fields.String(required=True)
