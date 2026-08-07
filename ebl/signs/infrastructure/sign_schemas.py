from typing import Dict

from marshmallow import EXCLUDE, Schema, fields, post_dump, post_load
from ebl.transliteration.domain.sign import (
    Sign,
    SignListRecord,
    Value,
    Logogram,
    Fossey,
    SortKeys,
)
from ebl.transliteration.application.museum_number_schema import MuseumNumberSchema

COLLECTION = "signs"


class SignListRecordSchema(Schema):
    name = fields.String(required=True)
    number = fields.String(required=True)

    @post_load
    def make_sign_list_record(self, data, **kwargs):
        return SignListRecord(**data)


class ValueSchema(Schema):
    value = fields.String(required=True)
    sub_index = fields.Int(load_default=None, data_key="subIndex")

    @post_load
    def make_value(self, data, **kwargs):
        return Value(**data)

    @post_dump
    def filter_none(self, data, **kwargs):
        return {key: value for key, value in data.items() if value is not None}


class OrderedSignSchema(Schema):
    name = fields.String(required=True)
    unicode = fields.List(fields.Int(), required=True)
    mzl = fields.String(required=False, data_key="mzlNumber")


class LogogramSchema(Schema):
    logogram = fields.String(required=True)
    atf = fields.String(required=True)
    word_id = fields.List(fields.String(), required=True, data_key="wordId")
    schramm_logogramme = fields.String(required=True, data_key="schrammLogogramme")
    unicode = fields.String()

    @post_load
    def make_logogram(self, data, **kwargs) -> Logogram:
        data["word_id"] = tuple(data["word_id"])
        return Logogram(**data)


class FosseySchema(Schema):
    page = fields.Integer(required=True)
    number = fields.Integer(required=True)
    suffix = fields.String(required=True)
    reference = fields.String(required=True)
    new_edition = fields.String(required=True, data_key="newEdition")
    secondary_literature = fields.String(required=True, data_key="secondaryLiterature")
    museum_number = fields.Nested(
        MuseumNumberSchema, required=True, allow_none=True, data_key="museumNumber"
    )
    cdli_number = fields.String(required=True, data_key="cdliNumber")
    external_project = fields.String(required=True, data_key="externalProject")
    notes = fields.String(required=True)
    date = fields.String(required=True)
    transliteration = fields.String(required=True)
    sign = fields.String(required=True)

    @post_load
    def make_fossey(self, data, **kwargs):
        return Fossey(**data)


class SortKeysSchema(Schema):
    neo_assyrian_onset = fields.List(
        fields.Integer(),
        data_key="neoAssyrianOnset",
        allow_none=True,
        load_default=None,
    )
    neo_babylonian_onset = fields.List(
        fields.Integer(),
        data_key="neoBabylonianOnset",
        allow_none=True,
        load_default=None,
    )
    neo_assyrian_offset = fields.List(
        fields.Integer(),
        data_key="neoAssyrianOffset",
        allow_none=True,
        load_default=None,
    )
    neo_babylonian_offset = fields.List(
        fields.Integer(),
        data_key="neoBabylonianOffset",
        allow_none=True,
        load_default=None,
    )

    @post_load
    def make_sort_keys(self, data, **kwargs) -> SortKeys:
        return SortKeys(**data)


class SignSchema(Schema):
    name = fields.String(required=True, data_key="_id")
    lists = fields.Nested(SignListRecordSchema, many=True, required=True)
    values = fields.Nested(ValueSchema, many=True, required=True, unknown=EXCLUDE)
    logograms = fields.Nested(LogogramSchema, many=True, load_default=())
    fossey = fields.Nested(FosseySchema, many=True, load_default=())
    mes_zl = fields.String(data_key="mesZl", load_default="", allow_none=True)
    labasi = fields.String(data_key="LaBaSi", load_default="", allow_none=True)
    reverse_order = fields.String(
        data_key="reverseOrder", load_default="", allow_none=True
    )
    unicode = fields.List(fields.Int(), load_default=())
    sort_keys = fields.Nested(
        SortKeysSchema,
        data_key="sortKeys",
        allow_none=True,
        load_default=None,
    )

    @post_load
    def make_sign(self, data, **kwargs) -> Sign:
        data["lists"] = tuple(data["lists"])
        data["values"] = tuple(data["values"])
        data["logograms"] = tuple(data["logograms"])
        data["fossey"] = tuple(data["fossey"])
        data["unicode"] = tuple(data["unicode"])
        return Sign(**data)

    @post_dump
    def filter_none(self, data, **kwargs):
        return {key: value for key, value in data.items() if value is not None}


class SignDtoSchema(SignSchema):
    @post_dump
    def make_sign_dto(self, data, **kwargs) -> Dict:
        data["name"] = data.pop("_id")
        return {key: value for key, value in data.items() if value is not None}
