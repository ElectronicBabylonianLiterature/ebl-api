from marshmallow import EXCLUDE, Schema, fields, post_dump, post_load
import pydash

from ebl.bibliography.application.reference_schema import ReferenceSchema
from ebl.common.application.schemas import AccessionSchema
from ebl.common.domain.period import Period, PeriodModifier
from ebl.fragmentarium.application.fragment_fields_schemas import (
    DossierReferenceSchema,
)
from ebl.fragmentarium.application.genre_schema import GenreSchema
from ebl.fragmentarium.domain.date import DateSchema
from ebl.fragmentarium.domain.fragment import Script
from ebl.fragmentarium.domain.fragment_query_summary import (
    FragmentQueryArchaeology,
    FragmentQueryResult,
    FragmentQuerySummary,
)
from ebl.schemas import ResearchProjectField, ValueEnumField
from ebl.transliteration.application.museum_number_schema import MuseumNumberSchema
from ebl.transliteration.application.text_schema import TextSchema
from ebl.transliteration.domain.text import Text


DEFAULT_THUMBNAIL_RESOLUTION = "small"


def deserialize_script_period(value):
    try:
        return Period.from_abbreviation(value)
    except ValueError:
        return Period.from_name(value)


class FragmentQueryScriptSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    period = fields.Function(
        lambda script: script.period.abbreviation,
        deserialize_script_period,
        required=True,
    )
    period_modifier = ValueEnumField(
        PeriodModifier, required=True, data_key="periodModifier"
    )
    uncertain = fields.Boolean(load_default=None)

    @post_load
    def make_script(self, data, **kwargs) -> Script:
        return Script(**data)


class FragmentQueryArchaeologySchema(Schema):
    class Meta:
        unknown = EXCLUDE

    excavation_number = fields.Nested(
        MuseumNumberSchema,
        allow_none=True,
        load_default=None,
        dump_default=None,
        data_key="excavationNumber",
    )
    site = fields.Method("serialize_site", "deserialize_site", allow_none=True)

    @staticmethod
    def serialize_site(obj):
        return {"name": obj.site} if obj.site else None

    @staticmethod
    def deserialize_site(value):
        if not value:
            return None
        if isinstance(value, dict):
            return value.get("name")
        return value

    @post_load
    def make_archaeology(self, data, **kwargs) -> FragmentQueryArchaeology:
        return FragmentQueryArchaeology(**data)

    @post_dump
    def filter_none(self, data, **kwargs):
        data = pydash.omit_by(data, pydash.is_none)
        return data or None


class FragmentQuerySummarySchema(Schema):
    class Meta:
        unknown = EXCLUDE

    museum_number = fields.Nested(
        MuseumNumberSchema, required=True, data_key="museumNumber"
    )
    accession = fields.Nested(
        AccessionSchema, allow_none=True, load_default=None, dump_default=None
    )
    description = fields.String(required=True)
    script = fields.Nested(FragmentQueryScriptSchema, required=True)
    date = fields.Nested(
        DateSchema, allow_none=True, load_default=None, dump_default=None
    )
    genres = fields.Nested(GenreSchema, many=True, load_default=())
    archaeology = fields.Nested(
        FragmentQueryArchaeologySchema,
        allow_none=True,
        load_default=None,
        dump_default=None,
    )
    references = fields.Nested(ReferenceSchema, many=True, load_default=())
    projects = fields.List(ResearchProjectField(), load_default=())
    dossiers = fields.Nested(DossierReferenceSchema, many=True, load_default=())
    matching_lines = fields.List(
        fields.Integer(), required=True, data_key="matchingLines"
    )
    matching_line_preview = fields.Nested(
        TextSchema,
        allow_none=True,
        load_default=None,
        dump_default=None,
        data_key="matchingLinePreview",
    )
    match_count = fields.Integer(required=True, data_key="matchCount")
    has_photo = fields.Boolean(required=True, data_key="hasPhoto")
    thumbnail_path = fields.Function(
        lambda summary: f"/fragments/{summary.museum_number}/thumbnail/{DEFAULT_THUMBNAIL_RESOLUTION}",
        dump_only=True,
        data_key="thumbnailPath",
    )

    @post_load
    def make_query_item(self, data, **kwargs) -> FragmentQuerySummary:
        data["matching_lines"] = tuple(data["matching_lines"])
        data["genres"] = tuple(data["genres"])
        data["references"] = tuple(data["references"])
        data["projects"] = tuple(data["projects"])
        data["dossiers"] = tuple(data["dossiers"])
        if data.get("matching_line_preview") is None:
            data["matching_line_preview"] = Text()
        return FragmentQuerySummary(**data)

    @post_dump(pass_many=True)
    def filter_none(self, data, many, **kwargs):
        if many:
            return [pydash.omit_by(item, pydash.is_none) for item in data]
        return pydash.omit_by(data, pydash.is_none)


class FragmentQueryResultSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    items = fields.Nested(FragmentQuerySummarySchema, many=True, required=True)
    match_count_total = fields.Integer(required=True, data_key="matchCountTotal")

    @post_load
    def make_query_result(self, data, **kwargs) -> FragmentQueryResult:
        data["items"] = tuple(data["items"])
        return FragmentQueryResult(**data)
