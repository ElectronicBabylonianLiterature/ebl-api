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
    ExcavationSite,
)
from ebl.schemas import NameEnumField
from marshmallow import Schema, fields, post_load


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


site_field = fields.Function(
    lambda object_: getattr(object_.site, "long_name", None),
    lambda value: ExcavationSite.from_name(value) if value else None,
    allow_none=True,
)


class FindspotSchema(Schema):
    id_ = fields.Integer(required=True, data_key="_id")
    site = site_field
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


class ArchaeologySchema(Schema):
    excavation_number = fields.Nested(
        ExcavationNumberSchema, data_key="excavationNumber", allow_none=True
    )
    site = site_field
    regular_excavation = fields.Boolean(
        load_default=False, data_key="isRegularExcavation"
    )
    excavation_date = fields.Nested(
        DateRangeSchema, allow_none=True, data_key="date", load_default=None
    )
    findspot_id = fields.Integer(allow_none=True, dump_default=None, load_default=None, data_key="findspotId")
    findspot = fields.Nested(FindspotSchema, allow_none=True, load_default=None)

    @post_load
    def create_archaeology(self, data, **kwargs) -> Archaeology:
        return Archaeology(**data)
