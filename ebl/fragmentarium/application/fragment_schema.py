import pydash
from marshmallow import Schema, fields, post_load, post_dump

from ebl.bibliography.domain.reference import BibliographyId, Reference, \
    ReferenceType
from ebl.fragmentarium.domain.folios import Folio, Folios
from ebl.fragmentarium.domain.fragment import (Fragment, FragmentNumber,
                                               Measure,
                                               UncuratedReference)
from ebl.fragmentarium.domain.record import (Record, RecordEntry, RecordType)
from ebl.transliteration.domain.text import Text


class MeasureSchema(Schema):
    value = fields.Float(missing=None)
    note = fields.String(missing=None)

    @post_load
    def make_measure(self, data, **kwargs):
        return Measure(**data)

    @post_dump
    def filter_none(self, data, **kwargs):
        return pydash.omit_by(data, pydash.is_none)


class RecordEntrySchema(Schema):
    user = fields.String(required=True)
    type = fields.Function(
        lambda entry: entry.type.value,
        lambda value: RecordType(value)
    )
    date = fields.String(required=True)

    @post_load
    def make_record_entry(self, data, **kwargs):
        return RecordEntry(**data)


class RecordSchema(Schema):
    entries = fields.Nested(RecordEntrySchema, many=True, required=True)

    @post_load
    def make_record(self, data, **kwargs):
        return Record(tuple(data['entries']))


class FolioSchema(Schema):
    name = fields.String(required=True)
    number = fields.String(required=True)

    @post_load
    def make_record_entry(self, data, **kwargs):
        return Folio(**data)


class FoliosSchema(Schema):
    entries = fields.Nested(FolioSchema, many=True, required=True)

    @post_load
    def make_folio(self, data, **kwargs):
        return Folios(tuple(data['entries']))


class ReferenceSchema(Schema):
    id = fields.String(required=True)
    type = fields.Function(
        lambda reference: reference.type.name,
        lambda type: ReferenceType[type]
    )
    pages = fields.String(required=True)
    notes = fields.String(required=True)
    lines_cited = fields.List(fields.String(),
                              required=True,
                              data_key='linesCited')

    @post_load
    def make_reference(self, data, **kwargs):
        data['id'] = BibliographyId(data['id'])
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
    record = fields.Pluck(RecordSchema, 'entries')
    folios: fields.Field = fields.Pluck(FoliosSchema, 'entries')
    text = fields.Function(
        lambda fragment: fragment.text.to_dict(),
        lambda text: Text.from_dict(text)
    )
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
        data['record'] = data['record']
        data['folios'] = data['folios']
        data['references'] = tuple(data['references'])
        if data['uncurated_references'] is not None:
            data['uncurated_references'] = tuple(data['uncurated_references'])
        return Fragment(**data)

    @post_dump
    def filter_none(self, data, **kwargs):
        return pydash.omit_by(data, pydash.is_none)
