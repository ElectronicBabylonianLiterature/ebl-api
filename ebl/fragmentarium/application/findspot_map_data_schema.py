from marshmallow import Schema, fields


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

    def serialize_findspot_id(self, obj):
        return obj.findspot.id_

    def serialize_site_id(self, obj):
        return obj.findspot.site.id if obj.findspot.site else None

    def serialize_site_name(self, obj):
        return obj.findspot.site.long_name if obj.findspot.site else None

    def serialize_polygon_ids(self, obj):
        if not obj.findspot.map_location:
            return []
        return list(obj.findspot.map_location.polygon_ids)

    def serialize_location_precision(self, obj):
        return obj.findspot.map_location.location_precision.value

    def serialize_match_method(self, obj):
        return obj.findspot.map_location.match_method.value

    def serialize_sector(self, obj):
        return obj.findspot.sector or None

    def serialize_area(self, obj):
        return obj.findspot.area or None

    def serialize_building(self, obj):
        return obj.findspot.building or None

    def serialize_room(self, obj):
        return obj.findspot.room or None
