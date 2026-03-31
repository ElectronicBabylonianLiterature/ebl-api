import math
from typing import Sequence
from pymongo.collation import Collation
from pymongo.database import Database

from ebl.provenance.application.provenance_repository import ProvenanceRepository
from ebl.provenance.application.provenance_schema import ProvenanceRecordSchema
from ebl.provenance.domain.provenance_model import ProvenanceRecord
from ebl.mongo_collection import MongoCollection

COLLECTION = "provenances"
_COLLATION = Collation(locale="en", strength=1, normalization=True)


class MongoProvenanceRepository(ProvenanceRepository):
    def __init__(self, database: Database):
        self._collection = MongoCollection(database, COLLECTION)

    def create_indexes(self) -> None:
        self._collection.create_index("longName", unique=False)
        self._collection.create_index("abbreviation", unique=False)
        self._collection.create_index("parent", unique=False)

    def create(self, provenance: ProvenanceRecord) -> str:
        return self._collection.insert_one(ProvenanceRecordSchema().dump(provenance))

    def find_all(self) -> Sequence[ProvenanceRecord]:
        cursor = (
            self._collection.find_many({}).sort("longName", 1).collation(_COLLATION)
        )
        return ProvenanceRecordSchema(many=True).load(cursor)

    def query_by_id(self, id_: str) -> ProvenanceRecord:
        data = self._collection.find_one_by_id(id_)
        return ProvenanceRecordSchema().load(data)

    def query_by_long_name(self, long_name: str) -> ProvenanceRecord:
        data = self._collection.find_one({"longName": long_name})
        return ProvenanceRecordSchema().load(data)

    def query_by_abbreviation(self, abbreviation: str) -> ProvenanceRecord:
        data = self._collection.find_one({"abbreviation": abbreviation})
        return ProvenanceRecordSchema().load(data)

    def find_children(self, parent: str) -> Sequence[ProvenanceRecord]:
        cursor = (
            self._collection.find_many({"parent": parent})
            .sort("longName", 1)
            .collation(_COLLATION)
        )
        return ProvenanceRecordSchema(many=True).load(cursor)

    def find_by_coordinates(
        self, latitude: float, longitude: float, radius_km: float
    ) -> Sequence[ProvenanceRecord]:
        lat_delta = radius_km / 111.0
        cos_latitude = math.cos(math.radians(latitude))
        longitude_denominator = 111.0 * abs(cos_latitude)
        lon_delta = (
            radius_km / longitude_denominator
            if longitude_denominator != 0
            else radius_km / 111.0
        )

        cursor = self._collection.find_many(
            {
                "coordinates.latitude": {
                    "$gte": latitude - lat_delta,
                    "$lte": latitude + lat_delta,
                },
                "coordinates.longitude": {
                    "$gte": longitude - lon_delta,
                    "$lte": longitude + lon_delta,
                },
            }
        )
        return ProvenanceRecordSchema(many=True).load(cursor)
