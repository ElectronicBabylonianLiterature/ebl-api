import attr
from typing import Dict, List, Sequence, Tuple

from marshmallow import Schema, fields, post_load, EXCLUDE
from pymongo.database import Database

from ebl.bibliography.application.reference_schema import ApiReferenceSchema
from ebl.bibliography.domain.reference import (
    BibliographyId,
    Reference,
    ReferenceType,
)
from ebl.common.query.query_collation import (
    CollatedFieldQuery,
    strip_realia_query_chars,
)
from ebl.errors import NotFoundError
from ebl.mongo_collection import MongoCollection
from ebl.realia.application.realia_repository import RealiaRepository
from ebl.realia.domain.realia_entry import (
    AfoRegisterEntry,
    RealiaEntry,
    ReallexikonEntry,
)
from ebl.realia.infrastructure.realia_search_ranking import RealiaRelevanceRanker

REALIA_COLLECTION = "realia"
BIBLIOGRAPHY_COLLECTION = "bibliography"


class ReallexikonReferenceField(fields.Field):
    def _serialize(self, value, attr_name, obj, **kwargs):
        return None if value is None else ApiReferenceSchema().dump(value)

    def _deserialize(self, value, attr_name, data, **kwargs):
        if isinstance(value, str):
            return Reference(BibliographyId(value), ReferenceType.DISCUSSION)
        return ApiReferenceSchema().load(value)


class AfoRegisterEntrySchema(Schema):
    class Meta:
        unknown = EXCLUDE

    main_word = fields.String(data_key="mainWord", load_default="")
    note = fields.String(load_default="")
    afo = fields.String(data_key="AfO", load_default="")
    reference = fields.String(load_default="")
    cross_reference = fields.String(data_key="crossReference", load_default="")

    @post_load
    def make_entry(self, data, **kwargs) -> AfoRegisterEntry:
        return AfoRegisterEntry(**data)


class ReallexikonEntrySchema(Schema):
    class Meta:
        unknown = EXCLUDE

    id = fields.String(load_default="")
    title = fields.String(load_default="")
    reference = ReallexikonReferenceField(allow_none=True, load_default=None)
    content = fields.String(load_default="")

    @post_load
    def make_entry(self, data, **kwargs) -> ReallexikonEntry:
        return ReallexikonEntry(**data)


class RealiaEntrySchema(Schema):
    class Meta:
        unknown = EXCLUDE

    id = fields.String(required=True, data_key="_id")
    related_terms = fields.List(
        fields.String(), data_key="relatedTerms", load_default=list
    )
    type = fields.List(fields.String(), load_default=list)
    afo_register = fields.List(
        fields.Nested(AfoRegisterEntrySchema), data_key="afoRegister", load_default=list
    )
    references = fields.Nested(ApiReferenceSchema, many=True, load_default=list)
    wikidata_id = fields.List(fields.String(), data_key="wikidataId", load_default=list)
    reallexikon = fields.List(fields.Nested(ReallexikonEntrySchema), load_default=list)

    @post_load
    def make_entry(self, data, **kwargs) -> RealiaEntry:
        data["related_terms"] = tuple(data["related_terms"])
        data["type"] = tuple(data["type"])
        data["afo_register"] = tuple(data["afo_register"])
        data["references"] = tuple(data["references"])
        data["wikidata_id"] = tuple(data["wikidata_id"])
        data["reallexikon"] = tuple(data["reallexikon"])
        return RealiaEntry(**data)


class MongoRealiaRepository(RealiaRepository):
    def __init__(self, database: Database) -> None:
        self._realia_collection = MongoCollection(database, REALIA_COLLECTION)
        self._bibliography_collection = MongoCollection(
            database, BIBLIOGRAPHY_COLLECTION
        )

    def find(self, realia_id: str) -> RealiaEntry:
        try:
            document = self._realia_collection.find_one_by_id(realia_id)
        except NotFoundError:
            raise NotFoundError(f"Realia entry '{realia_id}' not found.")
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

    def _inject_references(
        self, references: Sequence[Reference], bibliography: Dict[str, dict]
    ) -> Tuple[Reference, ...]:
        injected = [
            {**ApiReferenceSchema().dump(ref), "document": bibliography.get(ref.id, {})}
            for ref in references
        ]
        return tuple(ApiReferenceSchema(unknown=EXCLUDE, many=True).load(injected))

    def _inject_reallexikon(
        self, reallexikon: Sequence[ReallexikonEntry], bibliography: Dict[str, dict]
    ) -> Tuple[ReallexikonEntry, ...]:
        result = []
        for rlex in reallexikon:
            if rlex.reference is not None:
                injected = {
                    **ApiReferenceSchema().dump(rlex.reference),
                    "document": bibliography.get(rlex.reference.id, {}),
                }
                result.append(
                    attr.evolve(
                        rlex,
                        reference=ApiReferenceSchema(unknown=EXCLUDE).load(injected),
                    )
                )
            else:
                result.append(rlex)
        return tuple(result)
