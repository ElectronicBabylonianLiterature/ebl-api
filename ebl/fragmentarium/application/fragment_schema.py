from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, List, Optional, Type

import pydash
from marshmallow import Schema, fields, post_dump, post_load

from ebl.bibliography.domain.reference import (
    BibliographyId,
    Reference,
    ReferenceType,
)
from ebl.fragmentarium.domain.folios import Folio, Folios
from ebl.fragmentarium.domain.fragment import (
    Fragment,
    FragmentNumber,
    Measure,
    UncuratedReference,
)
from ebl.fragmentarium.domain.record import Record, RecordEntry, RecordType
from ebl.transliteration.domain.text import Text


class EnumField(fields.String, ABC):
    default_error_messages = {
        "invalid_value": "Invalid value.",
        "not_enum": "Not a valid Enum.",
    }

    def __init__(self, enum_class: Type[Enum], **kwargs):
        self._enum_class = enum_class
        super().__init__(enum=self._values(), **kwargs)

    def _serialize(self, value, attr, obj, **kwargs) -> Optional[str]:
        if isinstance(value, Enum):
            return super()._serialize(
                (self._serialize_enum(value) if value is not None else None),
                attr,
                obj,
                **kwargs
            )
        else:
            raise self.make_error("not_enum")

    def _deserialize(self, value, attr, data, **kwargs) -> Any:
        try:
            return self._deserialize_enum(
                super()._deserialize(value, attr, data, **kwargs)
            )
        except (KeyError, ValueError) as error:
            raise self.make_error("invalid_value") from error

    @abstractmethod
    def _serialize_enum(self, value: Enum) -> str:
        ...

    @abstractmethod
    def _deserialize_enum(self, value: str) -> Enum:
        ...

    @abstractmethod
    def _values(self) -> List[str]:
        ...


class ValueEnum(EnumField):
    def _serialize_enum(self, value: Enum) -> str:
        return value.value

    def _deserialize_enum(self, value: str) -> Enum:
        return self._enum_class(value)

    def _values(self) -> List[str]:
        return [e.value for e in self._enum_class]


class NameEnum(EnumField):
    def _serialize_enum(self, value: Enum) -> str:
        return value.name

    def _deserialize_enum(self, value: str) -> Enum:
        return self._enum_class[value]

    def _values(self) -> List[str]:
        return [e.name for e in self._enum_class]


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


class ReferenceSchema(Schema):
    id = fields.String(required=True)
    type = NameEnum(ReferenceType, required=True)
    pages = fields.String(required=True)
    notes = fields.String(required=True)
    lines_cited = fields.List(fields.String(), required=True, data_key="linesCited")
    document = fields.Mapping(missing=None, load_only=True)

    @post_load
    def make_reference(self, data, **kwargs):
        data["id"] = BibliographyId(data["id"])
        data["lines_cited"] = tuple(data["lines_cited"])
        return Reference(**data)


class UncuratedReferenceSchema(Schema):
    document = fields.String(required=True)
    pages = fields.List(fields.Integer(), required=True)

    @post_load
    def make_uncurated_reference(self, data, **kwargs):
        data["pages"] = tuple(data["pages"])
        return UncuratedReference(**data)


class FragmentSchema(Schema):
    number = fields.String(required=True, data_key="_id")
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
    folios: fields.Field = fields.Pluck(FoliosSchema, "entries")
    text = fields.Function(
        lambda fragment: fragment.text.to_dict(), lambda text: Text.from_dict(text),
    )
    signs = fields.String(missing=None)
    notes = fields.String(required=True)
    references = fields.Nested(ReferenceSchema, many=True, required=True)
    uncurated_references = fields.Nested(
        UncuratedReferenceSchema,
        many=True,
        data_key="uncuratedReferences",
        missing=None,
    )

    @post_load
    def make_fragment(self, data, **kwargs):
        data["number"] = FragmentNumber(data["number"])
        data["joins"] = tuple(data["joins"])
        data["record"] = data["record"]
        data["folios"] = data["folios"]
        data["references"] = tuple(data["references"])
        if data["uncurated_references"] is not None:
            data["uncurated_references"] = tuple(data["uncurated_references"])
        return Fragment(**data)

    @post_dump
    def filter_none(self, data, **kwargs):
        return pydash.omit_by(data, pydash.is_none)
