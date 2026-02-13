from ebl.common.application.schemas import AbstractMuseumNumberSchema
from ebl.bibliography.application.reference_schema import ReferenceSchema
from ebl.fragmentarium.application.date_schemas import (
    DateRangeSchema,
)
from ebl.fragmentarium.domain.archaeology import (
    Archaeology,
    ExcavationNumber,
)
from ebl.fragmentarium.domain.findspot import (
    BuildingType,
    ExcavationPlan,
    Findspot,
)
from ebl.schemas import NameEnumField
from marshmallow import Schema, fields, post_load, ValidationError


class ExcavationNumberSchema(AbstractMuseumNumberSchema):
    @post_load
    def create_excavation_number(self, data, **kwargs) -> ExcavationNumber:
        return ExcavationNumber(**data)


class ExcavationPlanSchema(Schema):
    svg = fields.String()
    references = fields.Nested(ReferenceSchema, many=True, load_default=())

    @post_load
    def create_excavation_plan(self, data, **kwargs) -> ExcavationPlan:
        data["references"] = tuple(data["references"])
        return ExcavationPlan(**data)


class ProvenanceSiteMixin:
    def _get_provenance_service(self):
        provenance_service = self.context.get("provenance_service")
        if provenance_service is None:
            raise ValidationError("Provenance service not configured.")
        return provenance_service

    def serialize_site(self, obj):
        return getattr(obj.site, "long_name", None)

    def deserialize_site(self, value):
        if value is None:
            return None
        provenance_service = self._get_provenance_service()
        record = provenance_service.find_by_name(value)
        if record is None:
            raise ValidationError(f"Invalid provenance: {value}")
        return record


class FindspotSchema(ProvenanceSiteMixin, Schema):
    id_ = fields.Integer(required=True, data_key="_id")
    site = fields.Method("serialize_site", "deserialize_site", allow_none=True)
    sector = fields.String()
    area = fields.String()
    building = fields.String()
    building_type = NameEnumField(
        BuildingType, data_key="buildingType", allow_none=True
    )
    lavel_layer_phase = fields.String(data_key="levelLayerPhase")
    date_range = fields.Nested(DateRangeSchema, data_key="date", allow_none=True)
    plans = fields.Nested(ExcavationPlanSchema, many=True, load_default=())
    room = fields.String()
    context = fields.String()
    primary_context = fields.Boolean(
        data_key="primaryContext",
        allow_none=True,
    )
    notes = fields.String()

    @post_load
    def create_findspot(self, data, **kwargs) -> Findspot:
        data["plans"] = tuple(data["plans"])
        return Findspot(**data)


class ArchaeologySchema(ProvenanceSiteMixin, Schema):
    excavation_number = fields.Nested(
        ExcavationNumberSchema, data_key="excavationNumber", allow_none=True
    )
    site = fields.Method("serialize_site", "deserialize_site", allow_none=True)
    regular_excavation = fields.Boolean(
        load_default=False, data_key="isRegularExcavation"
    )
    excavation_date = fields.Nested(
        DateRangeSchema, allow_none=True, data_key="date", load_default=None
    )
    findspot_id = fields.Integer(
        allow_none=True, dump_default=None, load_default=None, data_key="findspotId"
    )
    findspot = fields.Nested(FindspotSchema, allow_none=True, load_default=None)

    @post_load
    def create_archaeology(self, data, **kwargs) -> Archaeology:
        return Archaeology(**data)
