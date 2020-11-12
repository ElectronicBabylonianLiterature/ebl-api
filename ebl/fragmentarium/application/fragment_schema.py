import pydash  # pyre-ignore
from marshmallow import Schema, fields, post_dump, post_load  # pyre-ignore

from ebl.fragmentarium.application.genre_schema import GenreSchema
from ebl.bibliography.application.reference_schema import ReferenceSchema
from ebl.fragmentarium.domain.folios import Folio, Folios
from ebl.fragmentarium.domain.fragment import (
    Fragment,
    Measure,
    UncuratedReference,
    LineToVec,
)
from ebl.fragmentarium.domain.record import Record, RecordEntry, RecordType
from ebl.schemas import ValueEnum
from ebl.transliteration.application.text_schema import TextSchema
from ebl.fragmentarium.application.museum_number_schema import MuseumNumberSchema


class MeasureSchema(Schema):  # pyre-ignore[11]
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
    type = ValueEnum(RecordType, required=True)
    date = fields.String(required=True)

    @post_load
    def make_record_entry(self, data, **kwargs):
        return RecordEntry(**data)


class RecordSchema(Schema):
    entries = fields.Nested(RecordEntrySchema, many=True, required=True)

    @post_load
    def make_record(self, data, **kwargs):
        return Record(tuple(data["entries"]))


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
        return Folios(tuple(data["entries"]))


class UncuratedReferenceSchema(Schema):
    document = fields.String(required=True)
    pages = fields.List(fields.Integer(), required=True)

    @post_load
    def make_uncurated_reference(self, data, **kwargs):
        data["pages"] = tuple(data["pages"])
        return UncuratedReference(**data)


class LineToVecSchema(Schema):
    line_to_vec = fields.List(fields.Integer, required=True, data_key="lineToVec")
    complexity = fields.Int(required=True)

    @post_load
    def make_line_to_vec(self, data, **kwargs):
        return LineToVec(tuple(data["line_to_vec"]))


class FragmentSchema(Schema):
    number = fields.Nested(MuseumNumberSchema, required=True, data_key="museumNumber")
    accession = fields.String(required=True)
    cdli_number = fields.String(required=True, data_key="cdliNumber")
    bm_id_number = fields.String(required=True, data_key="bmIdNumber")
    publication = fields.String(required=True)
    description = fields.String(required=True)
    collection = fields.String(required=True)
    script = fields.String(required=True)
    museum = fields.String(required=True)
    width = fields.Nested(MeasureSchema, required=True)
    length = fields.Nested(MeasureSchema, required=True)
    thickness = fields.Nested(MeasureSchema, required=True)
    joins = fields.List(fields.String(), required=True)
    record = fields.Pluck(RecordSchema, "entries")
    folios = fields.Pluck(FoliosSchema, "entries")
    text = fields.Nested(TextSchema)
    signs = fields.String(missing="")
    notes = fields.String(required=True)
    references = fields.Nested(ReferenceSchema, many=True, required=True)
    uncurated_references = fields.Nested(
        UncuratedReferenceSchema,
        many=True,
        data_key="uncuratedReferences",
        missing=None,
    )
    genres = fields.Nested(GenreSchema, many=True, missing=tuple())
    line_to_vec = fields.Nested(LineToVecSchema, missing=None, data_key="lineToVec")

    @post_load
    def make_fragment(self, data, **kwargs):
        data["joins"] = tuple(data["joins"])
        data["references"] = tuple(data["references"])
        data["genres"] = tuple(data["genres"])
        if data["uncurated_references"] is not None:
            data["uncurated_references"] = tuple(data["uncurated_references"])
        return Fragment(**data)

    @post_dump
    def filter_none(self, data, **kwargs):
        return pydash.omit_by(data, pydash.is_none)
