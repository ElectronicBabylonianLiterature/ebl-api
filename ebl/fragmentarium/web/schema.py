from marshmallow import Schema, fields


class MeasureSchema(Schema):
    value = fields.Float(missing=None)
    note = fields.String(missing=None)


class RecordEntrySchema(Schema):
    user = fields.String(required=True)
    type = fields.Method('get_type')
    date = fields.String(required=True)

    def get_type(self, obj) -> str:
        return obj.type.value


class RecordSchema(Schema):
    entries = fields.Nested(RecordEntrySchema, many=True, required=True)


class FolioSchema(Schema):
    name = fields.String(required=True)
    number = fields.String(required=True)


class ReferenceSchema(Schema):
    id = fields.String(required=True)
    type = fields.Function(lambda reference: reference.type.name)
    pages = fields.String(required=True)
    notes = fields.String(required=True)
    lines_cited = fields.List(fields.String(),
                              required=True,
                              data_key='linesCited')
    document = None


class UncuratedReferenceSchema(Schema):
    document = fields.String(required=True)
    pages = fields.List(fields.Integer(), required=True)


class TextSchema(Schema):
    atf = fields.String(required=True)


class Text(fields.Field):
    def _serialize(self, value, attr, obj, **kwargs):
        return value.to_dict()


class FragmentSchema(Schema):
    number = fields.String(required=True, data_key='_id')
    accession = fields.String(required=True)
    cdli_number = fields.String(required=True, data_key='cdliNumber')
    bm_id_number = fields.String(required=True, data_key='bmIdNumber')
    publication = fields.String(required=True)
    description = fields.String(required=True)
    collection = fields.String(required=True)
    script = fields.String(required=True)
    museum = fields.String(required=True)
    width = fields.Nested(MeasureSchema, required=True)
    length = fields.Nested(MeasureSchema, required=True)
    thickness = fields.Nested(MeasureSchema, required=True)
    joins = fields.List(fields.String(), required=True)
    record = fields.Pluck(RecordSchema, 'entries')
    folios = fields.Function(
        lambda fragment, context: FolioSchema(many=True).dump(
            fragment.folios.filter(context['user']).entries
        )
    )
    text = Text()
    signs = fields.String(missing=None)
    notes = fields.String(required=True)
    references = fields.Nested(ReferenceSchema, many=True, required=True)
    uncurated_references = fields.Nested(UncuratedReferenceSchema,
                                         many=True,
                                         data_key='uncuratedReferences',
                                         missing=None)
    atf = fields.Pluck(TextSchema, 'atf', dump_only=True, attribute='text')
