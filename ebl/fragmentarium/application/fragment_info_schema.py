from marshmallow import Schema, fields

from ebl.bibliography.application.reference_schema import (
    ReferenceSchema,
    ApiReferenceSchema,
)
from ebl.common.application.schemas import AccessionSchema
from ebl.fragmentarium.application.fragment_fields_schemas import (
    AcquisitionSchema,
    ScriptSchema,
)
from ebl.fragmentarium.application.genre_schema import GenreSchema
from ebl.fragmentarium.domain.fragment_infos_pagination import FragmentInfosPagination
from ebl.transliteration.application.museum_number_schema import MuseumNumberSchema
from ebl.transliteration.application.text_schema import TextSchema


class FragmentInfoSchema(Schema):
    number: fields.Field = fields.Nested(MuseumNumberSchema, required=True)
    accession = fields.Nested(AccessionSchema, required=False)
    script = fields.Nested(ScriptSchema, required=True)
    acquisition = fields.Nested(AcquisitionSchema, required=False)
    description = fields.String(required=True)
    editor = fields.String(load_default="")
    edition_date = fields.String(data_key="editionDate", load_default="")
    matching_lines = fields.Nested(
        TextSchema, load_default=None, data_key="matchingLines"
    )
    references = fields.Nested(ReferenceSchema, many=True, load_default=())
    genres = fields.Nested(GenreSchema, many=True, load_default=())


class ApiFragmentInfoSchema(FragmentInfoSchema):
    number = fields.String(dump_only=True)
    references = fields.Nested(ApiReferenceSchema, many=True, required=True)


class ApiFragmentInfosPaginationSchema(Schema):
    class Meta:
        model = FragmentInfosPagination

    fragment_infos = fields.Nested(
        ApiFragmentInfoSchema,
        many=True,
        required=True,
        dump_only=True,
        data_key="fragmentInfos",
    )
    total_count = fields.Integer(required=True, dump_only=True, data_key="totalCount")
