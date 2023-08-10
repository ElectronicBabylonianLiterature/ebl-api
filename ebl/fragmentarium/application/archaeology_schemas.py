from ebl.bibliography.application.reference_schema import ReferenceSchema
from ebl.fragmentarium.application.date_range_schema import DateRangeSchema
from ebl.fragmentarium.domain.archaeology import Archaeology
from ebl.fragmentarium.domain.date import DateSchema
from ebl.fragmentarium.domain.findspot import BuildingType, ExcavationPlan, Findspot
from ebl.schemas import NameEnumField
from marshmallow import Schema, fields, post_load, validate
from ebl.transliteration.domain.museum_number import MuseumNumber as ExcavationNumber
from ebl.corpus.domain.manuscript import Provenance as ExcavationSite


class ExcavationNumberSchema(Schema):
    prefix = fields.String(required=True, validate=validate.Length(min=1))
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
        return Archaeology(**data)


class FindspotSchema(Schema):
    area = fields.String()
    building = fields.String()
    building_type = NameEnumField(BuildingType, data_key="buildingType")
    lavel_layer_phase = fields.String(data_key="lavelLayerPhase")
    date_range = fields.Nested(DateRangeSchema, data_key="dateRange")
    plans = fields.Nested(ExcavationPlanSchema, many=True, load_default=tuple())
    room = fields.String()
    context = fields.String()
    primary_context = fields.String(data_key="primaryContext")
    notes = fields.String()
    references = fields.Nested(ReferenceSchema, many=True, load_default=tuple())

    @post_load
    def create_findspot(self, data, **kwargs) -> Findspot:
        return Archaeology(**data)


class ArchaeologySchema(Schema):
    excavation_number = fields.Nested(
        ExcavationNumberSchema, required=True, data_key="excavationNumber"
    )
    site = fields.Function(
        lambda archaeology: archaeology.site.long_name,
        lambda value: ExcavationSite.from_name(value),
    )
    regular_excavation = fields.Boolean(load_default=True, data_key="regularExcavation")
    excavation_date = fields.Nested(
        DateSchema, data_key="excavationDate", many=True, allow_none=True, default=None
    )
    findspot = fields.Nested(FindspotSchema)

    @post_load
    def create_archaeology(self, data, **kwargs) -> Archaeology:
        return Archaeology(**data)
