import attr
import re
from typing import Sequence, List, Dict, Optional, Iterable, cast
from pymongo.database import Database
from ebl.mongo_collection import MongoCollection
from ebl.dossiers.domain.dossier_record import DossierRecord, DossierRecordSuggestion
from ebl.dossiers.infrastructure.dossiers_schemas import DossierRecordSchema
from ebl.dossiers.application.dossiers_repository import DossiersRepository
from ebl.bibliography.application.reference_documents import (
    bibliography_documents_by_lookup,
)
from ebl.bibliography.infrastructure.bibliography import MongoBibliographyRepository
from ebl.bibliography.domain.reference import BibliographyId
from ebl.provenance.application.provenance_service import ProvenanceService

DOSSIERS_COLLECTION = "dossiers"
FRAGMENTS_COLLECTION = "fragments"
MAX_QUERY_LENGTH = 256
MAX_SUGGESTION_WORDS = 7


class MongoDossiersRepository(DossiersRepository):
    def __init__(
        self, database: Database, provenance_service: ProvenanceService
    ) -> None:
        self._dossiers_collection = MongoCollection(database, DOSSIERS_COLLECTION)
        self._bibliography_repository = MongoBibliographyRepository(database)
        self._fragments_collection = MongoCollection(database, FRAGMENTS_COLLECTION)
        self._provenance_service = provenance_service

    def create(self, dossier_record: DossierRecord) -> str:
        return self._dossiers_collection.insert_one(
            DossierRecordSchema(
                context={"provenance_service": self._provenance_service}
            ).dump(dossier_record)
        )

    def find_all(self) -> Sequence[DossierRecord]:
        cursor = self._dossiers_collection.find_many({})
        dossiers = self._load_dossiers(cursor)
        reference_ids = self._extract_reference_ids(dossiers)
        bibliography_entries = self._fetch_bibliography_entries(reference_ids)
        self._inject_dossiers_with_bibliography(dossiers, bibliography_entries)
        return dossiers

    def query_by_ids(self, ids: Sequence[str]) -> Sequence[DossierRecord]:
        dossiers = self._fetch_dossiers(ids)
        reference_ids = self._extract_reference_ids(dossiers)
        bibliography_entries = self._fetch_bibliography_entries(reference_ids)
        self._inject_dossiers_with_bibliography(dossiers, bibliography_entries)
        return dossiers

    def search(
        self,
        query: str,
        provenance: Optional[str] = None,
        script_period: Optional[str] = None,
    ) -> Sequence[DossierRecord]:
        if not query:
            return []

        safe_query = re.escape(query[:MAX_QUERY_LENGTH])

        filters: List[Dict] = [
            {
                "$or": [
                    {"_id": {"$regex": safe_query, "$options": "i"}},
                    {"description": {"$regex": safe_query, "$options": "i"}},
                ]
            }
        ]

        if provenance:
            filters.append({"provenance": provenance})

        if script_period:
            filters.append({"script.period": script_period})

        search_filter = {"$and": filters} if len(filters) > 1 else filters[0]

        cursor = self._dossiers_collection.find_many(search_filter).limit(10)
        dossiers = self._load_dossiers(cursor)

        reference_ids = self._extract_reference_ids(dossiers)
        bibliography_entries = self._fetch_bibliography_entries(reference_ids)
        self._inject_dossiers_with_bibliography(dossiers, bibliography_entries)

        return dossiers

    def search_suggestions(self, query: str) -> Sequence[DossierRecordSuggestion]:
        if query:
            safe_query = re.escape(query[:MAX_QUERY_LENGTH])
            search_filter = {
                "$or": [
                    {"_id": {"$regex": safe_query, "$options": "i"}},
                    {"description": {"$regex": safe_query, "$options": "i"}},
                ]
            }
        else:
            search_filter = {}

        pipeline = [
            {"$match": search_filter},
            {
                "$project": {
                    "_id": 1,
                    "description": 1,
                }
            },
            {"$limit": 10},
        ]

        results = list(self._dossiers_collection.aggregate(pipeline))

        suggestions = []
        for result in results:
            description = result.get("description", "")
            words = description.split() if description else []
            snippet = " ".join(words[:MAX_SUGGESTION_WORDS])
            suggestions.append(
                DossierRecordSuggestion(id=result["_id"], description_snippet=snippet)
            )

        return suggestions

    def filter_by_fragment_criteria(
        self,
        provenance: Optional[str] = None,
        script_period: Optional[str] = None,
        genre: Optional[str] = None,
    ) -> Sequence[DossierRecord]:
        if not any([provenance, script_period, genre]):
            return self.find_all()

        try:
            fragment_query = self._build_fragment_query(
                provenance, script_period, genre
            )
            dossier_ids = self._extract_dossier_ids_from_fragments(fragment_query)

            if not dossier_ids:
                return []

            return self.query_by_ids(dossier_ids)
        except Exception:
            return []

    def _build_fragment_query(
        self,
        provenance: Optional[str],
        script_period: Optional[str],
        genre: Optional[str],
    ) -> Dict:
        fragment_filters = []

        if provenance:
            fragment_filters.append({"archaeology.site": provenance})

        if script_period:
            fragment_filters.append({"script.period": script_period})

        if genre:
            fragment_filters.append(self._build_genre_filter(genre))

        return (
            {"$and": fragment_filters}
            if len(fragment_filters) > 1
            else fragment_filters[0]
        )

    def _build_genre_filter(self, genre: str) -> Dict:
        genre_parts = genre.split(":")
        if len(genre_parts) == 1:
            return {"genres.category.0": genre_parts[0]}
        else:
            genre_filters = [
                {f"genres.category.{index}": part}
                for index, part in enumerate(genre_parts)
            ]
            return (
                {"$and": genre_filters} if len(genre_filters) > 1 else genre_filters[0]
            )

    def _extract_dossier_ids_from_fragments(self, fragment_query: Dict) -> List[str]:
        matching_fragments = self._fragments_collection.find_many(
            fragment_query, projection={"dossiers": 1}
        )

        dossier_ids = set()
        for fragment in matching_fragments:
            for dossier_ref in fragment.get("dossiers", []):
                dossier_id = self._extract_dossier_id(dossier_ref)
                if dossier_id:
                    dossier_ids.add(dossier_id)

        return list(dossier_ids)

    def _extract_dossier_id(self, dossier_ref) -> Optional[str]:
        if isinstance(dossier_ref, dict):
            return dossier_ref.get("dossierId")
        elif isinstance(dossier_ref, str):
            return dossier_ref
        return None

    def _fetch_dossiers(self, ids: Sequence[str]) -> List[DossierRecord]:
        cursor = self._dossiers_collection.find_many({"_id": {"$in": ids}})
        return self._load_dossiers(cursor)

    def _extract_reference_ids(
        self, dossiers: List[DossierRecord]
    ) -> List[BibliographyId]:
        return list(
            {reference.id for dossier in dossiers for reference in dossier.references}
        )

    def _fetch_bibliography_entries(
        self, reference_ids: List[BibliographyId]
    ) -> Dict[str, dict]:
        return bibliography_documents_by_lookup(
            reference_ids, self._bibliography_repository
        )

    def _load_dossiers(self, documents: Iterable[dict]) -> List[DossierRecord]:
        return cast(
            List[DossierRecord],
            DossierRecordSchema(
                many=True, context={"provenance_service": self._provenance_service}
            ).load(documents),
        )

    def _inject_dossiers_with_bibliography(
        self, dossiers: List[DossierRecord], bibliography_entries: Dict[str, dict]
    ) -> None:
        for index, dossier in enumerate(dossiers):
            dossiers[index] = attr.evolve(
                dossier,
                references=tuple(
                    attr.evolve(
                        reference, document=bibliography_entries.get(reference.id, {})
                    )
                    for reference in dossier.references
                ),
            )
