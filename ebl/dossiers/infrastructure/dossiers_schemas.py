from typing import Optional

from marshmallow import EXCLUDE, Schema, fields, post_load

from ebl.bibliography.application.reference_schema import ApiReferenceSchema
from ebl.common.application.schemas import deserialize_provenance_record
from ebl.dossiers.domain.dossier_record import DossierRecord, DossierRecordSuggestion
from ebl.fragmentarium.application.fragment_fields_schemas import ScriptSchema


class DossierRecordSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    id = fields.String(required=True, data_key="_id", metadata={"unique": True})
    description = fields.String(load_default=None)
    is_approximate_date = fields.Boolean(
        data_key="isApproximateDate", load_default=False
    )
    year_range_from = fields.Integer(
        data_key="yearRangeFrom", allow_none=True, load_default=None
    )
    year_range_to = fields.Integer(
        data_key="yearRangeTo", allow_none=True, load_default=None
    )
    related_kings = fields.List(
        fields.Float(), data_key="relatedKings", load_default=list
    )
    provenance = fields.Method(
        "serialize_provenance",
        "deserialize_provenance",
        allow_none=True,
    )
    script = fields.Nested(ScriptSchema, allow_none=True, load_default=None)
    references = fields.Nested(
        ApiReferenceSchema, allow_none=True, many=True, load_default=()
    )

    @post_load
    def make_record(self, data, **kwargs):
        data["references"] = tuple(data["references"])
        return DossierRecord(**data)

    def serialize_provenance(self, record: DossierRecord) -> Optional[str]:
        return getattr(record.provenance, "long_name", None)

    def deserialize_provenance(self, value: Optional[str]):
        return deserialize_provenance_record(self, value)


class DossierRecordSuggestionSchema(Schema):
    id = fields.String(required=True)
    description_snippet = fields.String(required=True, data_key="descriptionSnippet")

    @post_load
    def make_suggestion(self, data, **kwargs):
        return DossierRecordSuggestion(**data)
