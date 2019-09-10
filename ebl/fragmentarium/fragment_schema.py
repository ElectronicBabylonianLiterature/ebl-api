from marshmallow import Schema, fields, post_load

from ebl.bibliography.reference import BibliographyId, Reference, ReferenceType
from ebl.fragment.folios import Folio, Folios
from ebl.fragment.fragment import (Fragment, FragmentNumber, Measure,
                                   UncuratedReference)
from ebl.fragment.record import (Record, RecordEntry, RecordType)
from ebl.text.text import Text


class MeasureSchema(Schema):
    value = fields.Float(missing=None)
    note = fields.String(missing=None)

    @post_load
    def make_measure(self, data, **kwargs):
        return Measure(**data)


class RecordEntrySchema(Schema):
    user = fields.String(required=True)
    type = fields.String(required=True)
    date = fields.String(required=True)

    @post_load
    def make_record_entry(self, data, **kwargs):
        data['type'] = RecordType(data['type'])
        return RecordEntry(**data)


class FolioSchema(Schema):
    name = fields.String(required=True)
    number = fields.String(required=True)

    @post_load
    def make_record_entry(self, data, **kwargs):
        return Folio(**data)


class ReferenceSchema(Schema):
    id = fields.String(required=True)
    type = fields.String(required=True)
    pages = fields.String(required=True)
    notes = fields.String(required=True)
    lines_cited = fields.List(fields.String(),
                              required=True,
                              data_key='linesCited')
    document = fields.Mapping(missing=None)

    @post_load
    def make_reference(self, data, **kwargs):
        data['id'] = BibliographyId(data['id'])
        data['type'] = ReferenceType[data['type']]
        data['lines_cited'] = tuple(data['lines_cited'])
        return Reference(**data)


class UncuratedReferenceSchema(Schema):
    document = fields.String(required=True)
    pages = fields.List(fields.Integer(), required=True)

    @post_load
    def make_uncurated_reference(self, data, **kwargs):
        data['pages'] = tuple(data['pages'])
        return UncuratedReference(**data)


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
    record = fields.Nested(RecordEntrySchema, many=True, required=True)
    folios = fields.Nested(FolioSchema, many=True, required=True)
    text = fields.Mapping(fields.String(), required=True)
    signs = fields.String(missing=None)
    notes = fields.String(required=True)
    references = fields.Nested(ReferenceSchema, many=True, required=True)
    uncurated_references = fields.Nested(UncuratedReferenceSchema,
                                         many=True,
                                         data_key='uncuratedReferences',
                                         missing=None)

    @post_load
    def make_fragment(self, data, **kwargs):
        data['number'] = FragmentNumber(data['number'])
        data['joins'] = tuple(data['joins'])
        data['record'] = Record(tuple(data['record']))
        data['folios'] = Folios(tuple(data['folios']))
        data['text'] = Text.from_dict(data['text'])
        data['references'] = tuple(data['references'])
        if data['uncurated_references'] is not None:
            data['uncurated_references'] = tuple(data['uncurated_references'])
        return Fragment(**data)
