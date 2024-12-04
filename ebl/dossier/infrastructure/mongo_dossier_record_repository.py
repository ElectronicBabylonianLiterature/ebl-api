from marshmallow import Schema, fields, post_load, EXCLUDE
from pymongo.database import Database
from ebl.mongo_collection import MongoCollection
from ebl.dossier.domain.dossier_record import DossierRecord
from ebl.dossier.application.dossier_repository import DossierRepository
from ebl.common.domain.provenance import Provenance
from ebl.fragmentarium.application.fragment_schema import ScriptSchema
from ebl.schemas import NameEnumField
from ebl.bibliography.domain.reference import ReferenceType

COLLECTION = "dossier"

provenance_field = fields.Function(
    lambda object_: getattr(object_.site, "long_name", None),
    lambda value: Provenance.from_name(value) if value else None,
    allow_none=True,
)


class DossierRecordSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    id: fields.Integer(required=True)
    name: fields.String(required=True)
    description: fields.String(required=True)
    is_approximate_date: fields.Boolean(load_default=False)
    year_range_from: fields.String(
        data_key="yearRangeFrom", allow_none=True, load_default=None
    )
    year_range_to: fields.String(
        data_key="yearRangeTo", allow_none=True, load_default=None
    )
    related_kings: fields.List(fields.Integer(), data_key="relatedKings")
    provenance: provenance_field
    script: fields.Nested(ScriptSchema, required=True, load_default=())
    references: fields.Nested(
        NameEnumField(ReferenceType, required=True), required=True, many=True
    )

    @post_load
    def make_record(self, data, **kwargs):
        return DossierRecord(**data)


class MongoDossierRepository(DossierRepository):
    def __init__(self, database: Database):
        self._afo_register = MongoCollection(database, COLLECTION)

    def fetch(self, query, *args, **kwargs) -> DossierRecord:
        return
