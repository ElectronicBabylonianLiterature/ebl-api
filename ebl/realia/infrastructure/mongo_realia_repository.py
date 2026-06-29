import attr
from typing import Dict, List, Sequence, Tuple

from pymongo.database import Database

from ebl.bibliography.application.serialization import create_object_entry
from ebl.bibliography.domain.reference import BibliographyId, Reference
from ebl.common.query.query_collation import (
    CollatedFieldQuery,
    strip_realia_query_chars,
)
from ebl.errors import NotFoundError
from ebl.mongo_collection import MongoCollection
from ebl.realia.application.realia_repository import RealiaRepository
from ebl.realia.domain.realia_entry import RealiaEntry, ReallexikonEntry
from ebl.realia.infrastructure.realia_schemas import RealiaEntrySchema
from ebl.realia.infrastructure.realia_search_ranking import RealiaRelevanceRanker

REALIA_COLLECTION = "realia"
BIBLIOGRAPHY_COLLECTION = "bibliography"


class MongoRealiaRepository(RealiaRepository):
    def __init__(self, database: Database) -> None:
        self._realia_collection = MongoCollection(database, REALIA_COLLECTION)
        self._bibliography_collection = MongoCollection(
            database, BIBLIOGRAPHY_COLLECTION
        )

    def create_indexes(self) -> None:
        self._realia_collection.create_index(
            "realiaId",
            unique=True,
            partialFilterExpression={"realiaId": {"$gt": ""}},
        )

    def find(self, id_: str) -> RealiaEntry:
        try:
            document = self._realia_collection.find_one_by_id(id_)
        except NotFoundError:
            raise NotFoundError(f"Realia entry '{id_}' not found.")
        return self._load_entry(document)

    def find_by_realia_id(self, realia_id: str) -> RealiaEntry:
        try:
            document = self._realia_collection.find_one({"realiaId": realia_id})
        except NotFoundError:
            raise NotFoundError(f"Realia entry with realiaId '{realia_id}' not found.")
        return self._load_entry(document)

    def _load_entry(self, document: dict) -> RealiaEntry:
        entries = [RealiaEntrySchema().load(document)]
        self._inject_bibliography(entries)
        return entries[0]

    def search(self, query: str) -> Sequence[RealiaEntry]:
        stripped = strip_realia_query_chars(query).strip()
        if not stripped:
            return []
        ranker = RealiaRelevanceRanker(stripped)
        documents = sorted(
            self._realia_collection.find_many(self._build_search_query(stripped)),
            key=ranker.key,
        )
        entries = RealiaEntrySchema(many=True).load(documents)
        self._inject_bibliography(entries)
        return entries

    def _make_regex_condition(self, cfq: CollatedFieldQuery) -> dict:
        options = "i" if cfq.use_collations else ""
        return {"$regex": cfq.value, "$options": options}

    def _build_search_query(self, stripped: str) -> dict:
        id_cfq = CollatedFieldQuery(stripped, "_id", "realia")
        terms_cfq = CollatedFieldQuery(stripped, "relatedTerms", "realia")
        return {
            "$or": [
                {"_id": self._make_regex_condition(id_cfq)},
                {"relatedTerms": self._make_regex_condition(terms_cfq)},
            ]
        }

    def _collect_reference_ids(
        self, entries: List[RealiaEntry]
    ) -> List[BibliographyId]:
        ids: set[BibliographyId] = set()
        for entry in entries:
            for ref in entry.references:
                ids.add(ref.id)
            for rlex in entry.reallexikon:
                if rlex.reference is not None:
                    ids.add(rlex.reference.id)
        return list(ids)

    def _fetch_bibliography_entries(
        self, reference_ids: List[BibliographyId]
    ) -> Dict[str, dict]:
        entries = self._bibliography_collection.find_many(
            {"_id": {"$in": reference_ids}}
        )
        return {entry["_id"]: entry for entry in entries}

    def _inject_bibliography(self, entries: List[RealiaEntry]) -> None:
        bibliography = self._fetch_bibliography_entries(
            self._collect_reference_ids(entries)
        )
        for index, entry in enumerate(entries):
            entries[index] = self._inject_entry(entry, bibliography)

    def _inject_entry(
        self, entry: RealiaEntry, bibliography: Dict[str, dict]
    ) -> RealiaEntry:
        return attr.evolve(
            entry,
            references=self._inject_references(entry.references, bibliography),
            reallexikon=self._inject_reallexikon(entry.reallexikon, bibliography),
        )

    def _document_for(
        self, reference_id: BibliographyId, bibliography: Dict[str, dict]
    ) -> dict:
        document = bibliography.get(reference_id)
        return create_object_entry(document) if document else {}

    def _inject_references(
        self, references: Sequence[Reference], bibliography: Dict[str, dict]
    ) -> Tuple[Reference, ...]:
        return tuple(
            reference.set_document(self._document_for(reference.id, bibliography))
            for reference in references
        )

    def _inject_reallexikon(
        self, reallexikon: Sequence[ReallexikonEntry], bibliography: Dict[str, dict]
    ) -> Tuple[ReallexikonEntry, ...]:
        return tuple(
            (
                rlex
                if rlex.reference is None
                else attr.evolve(
                    rlex,
                    reference=rlex.reference.set_document(
                        self._document_for(rlex.reference.id, bibliography)
                    ),
                )
            )
            for rlex in reallexikon
        )
