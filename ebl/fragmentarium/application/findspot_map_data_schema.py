from marshmallow import Schema, fields

from ebl.fragmentarium.application.findspot_map_data_service import FindspotMapData


class FindspotMapDataSchema(Schema):
    findspot_id = fields.Method("serialize_findspot_id", data_key="findspotId")
    site_id = fields.Method("serialize_site_id", data_key="siteId")
    site_name = fields.Method("serialize_site_name", data_key="siteName")
    polygon_ids = fields.Method("serialize_polygon_ids", data_key="polygonIds")
    accessible_fragment_count = fields.Integer(
        data_key="accessibleFragmentCount", dump_only=True
    )
    location_precision = fields.Method(
        "serialize_location_precision", data_key="locationPrecision"
    )
    match_method = fields.Method("serialize_match_method", data_key="matchMethod")
    sector = fields.Method("serialize_sector")
    area = fields.Method("serialize_area")
    building = fields.Method("serialize_building")
    room = fields.Method("serialize_room")

    def serialize_findspot_id(self, obj: FindspotMapData) -> int:
        return obj.findspot.id_

    def serialize_site_id(self, obj: FindspotMapData) -> str:
        return obj.site_id

    def serialize_site_name(self, obj: FindspotMapData) -> str:
        return obj.site_name

    def serialize_polygon_ids(self, obj: FindspotMapData) -> list[str]:
        return list(obj.map_location.polygon_ids)

    def serialize_location_precision(self, obj: FindspotMapData) -> str:
        return obj.map_location.location_precision.value

    def serialize_match_method(self, obj: FindspotMapData) -> str:
        return obj.map_location.match_method.value

    def serialize_sector(self, obj: FindspotMapData) -> str | None:
        return obj.findspot.sector or None

    def serialize_area(self, obj: FindspotMapData) -> str | None:
        return obj.findspot.area or None

    def serialize_building(self, obj: FindspotMapData) -> str | None:
        return obj.findspot.building or None

    def serialize_room(self, obj: FindspotMapData) -> str | None:
        return obj.findspot.room or None
