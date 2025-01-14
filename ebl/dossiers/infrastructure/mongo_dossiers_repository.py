import attr
from typing import Sequence, List, Dict
from marshmallow import Schema, fields, post_load, EXCLUDE
from pymongo.database import Database
from ebl.mongo_collection import MongoCollection
from ebl.dossiers.domain.dossier_record import (
    DossierRecord,
)
from ebl.dossiers.application.dossiers_repository import DossiersRepository
from ebl.common.domain.provenance import Provenance
from ebl.fragmentarium.application.fragment_fields_schemas import ScriptSchema
from ebl.bibliography.application.reference_schema import ReferenceSchema
from ebl.bibliography.domain.reference import BibliographyId

DOSSIERS_COLLECTION = "dossiers"
BIBLIOGRAPHY_COLLECTION = "bibliography"


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
    provenance = fields.Function(
        lambda object_: getattr(object_.provenance, "long_name", None),
        lambda value: Provenance.from_name(value) if value else None,
        allow_none=True,
    )
    script = fields.Nested(ScriptSchema, allow_none=True, load_default=None)
    references = fields.Nested(
        ReferenceSchema, allow_none=True, many=True, load_default=()
    )

    @post_load
    def make_record(self, data, **kwargs):
        data["references"] = tuple(data["references"])
        return DossierRecord(**data)


class MongoDossiersRepository(DossiersRepository):
    def __init__(self, database: Database):
        self._dossiers_collection = MongoCollection(database, DOSSIERS_COLLECTION)
        self._bibliography_collection = MongoCollection(
            database, BIBLIOGRAPHY_COLLECTION
        )

    def create(self, dossier_record: DossierRecord) -> str:
        return self._dossiers_collection.insert_one(
            DossierRecordSchema().dump(dossier_record)
        )

    def query_by_ids(self, ids: Sequence[str]) -> Sequence[DossierRecord]:
        dossiers = self._fetch_dossiers(ids)
        reference_ids = self._extract_reference_ids(dossiers)
        bibliography_entries = self._fetch_bibliography_entries(reference_ids)
        self._inject_dossiers_with_bibliography(dossiers, bibliography_entries)
        return dossiers

    def _fetch_dossiers(self, ids: Sequence[str]) -> List[DossierRecord]:
        cursor = self._dossiers_collection.find_many({"_id": {"$in": ids}})
        return DossierRecordSchema(many=True).load(cursor)

    def _extract_reference_ids(
        self, dossiers: List[DossierRecord]
    ) -> List[BibliographyId]:
        return list(
            {reference.id for dossier in dossiers for reference in dossier.references}
        )

    def _fetch_bibliography_entries(
        self, reference_ids: List[BibliographyId]
    ) -> Dict[str, dict]:
        entries = self._bibliography_collection.find_many(
            {"_id": {"$in": reference_ids}}
        )
        return {entry["_id"]: entry for entry in entries}

    def _inject_dossiers_with_bibliography(
        self, dossiers: List[DossierRecord], bibliography_entries: Dict[str, dict]
    ) -> None:
        for index, dossier in enumerate(dossiers):
            injected_references = [
                {
                    **ReferenceSchema().dump(reference),
                    "document": bibliography_entries.get(reference.id, {}),
                }
                for reference in dossier.references
            ]
            dossiers[index] = attr.evolve(
                dossier,
                references=ReferenceSchema(unknown=EXCLUDE, many=True).load(
                    injected_references
                ),
            )
