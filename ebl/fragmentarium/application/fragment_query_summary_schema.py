from marshmallow import EXCLUDE, Schema, fields, post_dump, post_load
import pydash

from ebl.common.application.schemas import AccessionSchema
from ebl.fragmentarium.application.fragment_fields_schemas import ScriptSchema
from ebl.fragmentarium.application.genre_schema import GenreSchema
from ebl.fragmentarium.domain.date import DateSchema
from ebl.fragmentarium.domain.fragment_query_summary import (
    FragmentQueryResult,
    FragmentQuerySummary,
)
from ebl.transliteration.application.museum_number_schema import MuseumNumberSchema


DEFAULT_THUMBNAIL_RESOLUTION = "small"


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
    script = fields.Nested(ScriptSchema, required=True)
    date = fields.Nested(
        DateSchema, allow_none=True, load_default=None, dump_default=None
    )
    genres = fields.Nested(GenreSchema, many=True, load_default=())
    matching_lines = fields.List(
        fields.Integer(), required=True, data_key="matchingLines"
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
