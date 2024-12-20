from typing import Sequence
from marshmallow import Schema, fields, post_load, EXCLUDE
from pymongo.database import Database
from ebl.mongo_collection import MongoCollection
from ebl.dossiers.domain.dossier_record import (
    DossierRecord,
)
from ebl.dossiers.application.dossiers_repository import DossiersRepository
from ebl.common.domain.provenance import Provenance
from ebl.fragmentarium.application.fragment_fields_schemas import ScriptSchema
from ebl.schemas import NameEnumField
from ebl.bibliography.domain.reference import ReferenceType

COLLECTION = "dossier"

provenance_field = fields.Function(
    lambda object_: getattr(object_.provenance, "long_name", None),
    lambda value: Provenance.from_name(value) if value else None,
    allow_none=True,
)


class DossierRecordSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    id = fields.String(required=True, unique=True, data_key="_id")
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
    provenance = provenance_field
    script = fields.Nested(ScriptSchema, allow_none=True, load_default=None)
    references = fields.List(NameEnumField(ReferenceType), load_default=list)

    @post_load
    def make_record(self, data, **kwargs):
        return DossierRecord(**data)


class MongoDossiersRepository(DossiersRepository):
    def __init__(self, database: Database):
        self._collection = MongoCollection(database, COLLECTION)

    def query_by_ids(self, ids: Sequence[str]) -> Sequence[DossierRecord]:
        cursor = self._collection.find_many({"_id": {"$in": ids}})
        return DossierRecordSchema(many=True).load(cursor)

    def create(self, dossier_record: DossierRecord) -> str:
        return self._collection.insert_one(DossierRecordSchema().dump(dossier_record))
