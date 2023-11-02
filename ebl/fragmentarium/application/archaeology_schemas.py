from ebl.bibliography.application.reference_schema import ReferenceSchema
from ebl.fragmentarium.application.date_schemas import (
    DateRangeSchema,
    DateWithNotesSchema,
)
from ebl.fragmentarium.domain.archaeology import Archaeology
from ebl.fragmentarium.domain.findspot import BuildingType, ExcavationPlan, Findspot
from ebl.schemas import NameEnumField
from marshmallow import Schema, fields, post_load, validate
from ebl.transliteration.domain.museum_number import MuseumNumber as ExcavationNumber
from ebl.corpus.domain.provenance import Provenance as ExcavationSite


class ExcavationNumberSchema(Schema):
    prefix = fields.String(
        required=True, validate=(validate.Length(min=1), validate.ContainsNoneOf("."))
    )
    number = fields.String(
        required=True, validate=(validate.Length(min=1), validate.ContainsNoneOf("."))
    )
    suffix = fields.String(required=True, validate=validate.ContainsNoneOf("."))

    @post_load
    def create_excavation_number(self, data, **kwargs) -> ExcavationNumber:
        return ExcavationNumber(**data)


class ExcavationPlanSchema(Schema):
    svg = fields.String()
    references = fields.Nested(ReferenceSchema, many=True, load_default=tuple())

    @post_load
    def create_excavation_plan(self, data, **kwargs) -> ExcavationPlan:
        data["references"] = tuple(data["references"])
        return ExcavationPlan(**data)


class FindspotSchema(Schema):
    id_ = fields.Integer(required=True, data_key="_id")
    site = fields.Function(
        lambda findspot: getattr(findspot.site, "long_name", None),
        lambda value: ExcavationSite.from_name(value),
        allow_none=True,
    )
    area = fields.String()
    building = fields.String()
    building_type = NameEnumField(BuildingType, data_key="buildingType")
    lavel_layer_phase = fields.String(data_key="levelLayerPhase")
    date_range = fields.Nested(DateRangeSchema, data_key="dateRange", allow_none=True)
    plans = fields.Nested(ExcavationPlanSchema, many=True, load_default=tuple())
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
    site = fields.Function(
        lambda archaeology: getattr(archaeology.site, "long_name", None),
        lambda value: ExcavationSite.from_name(value),
        allow_none=True,
    )
    regular_excavation = fields.Boolean(
        load_default=True, data_key="isRegularExcavation"
    )
    excavation_date = fields.Nested(
        DateWithNotesSchema, data_key="excavationDate", many=True, load_default=tuple()
    )
    findspot_id = fields.Integer(allow_none=True, default=None, data_key="findspotId")
    findspot = fields.Nested(
        FindspotSchema, allow_none=True, default=None, data_key="findspot"
    )

    @post_load
    def create_archaeology(self, data, **kwargs) -> Archaeology:
        data["excavation_date"] = tuple(data["excavation_date"])
        return Archaeology(**data)
