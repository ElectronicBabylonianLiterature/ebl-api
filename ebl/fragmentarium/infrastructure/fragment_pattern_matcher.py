from typing import List, Dict, Sequence, Optional
from ebl.common.domain.scopes import Scope
from ebl.fragmentarium.infrastructure.queries import (
    match_user_scopes,
    number_is,
)
from ebl.fragmentarium.infrastructure.fragment_lemma_matcher import (
    LemmaMatcher,
    EmptyMatcher,
)
from ebl.common.query.query_result import LemmaQueryType
from ebl.fragmentarium.infrastructure.fragment_sign_matcher import SignMatcher
from ebl.fragmentarium.infrastructure.fragment_query_result_projection import (
    count_is_exact,
    count_pipeline,
    items_pipeline,
    result_projection,
)
from ebl.provenance.application.provenance_service import ProvenanceService
from ebl.provenance.domain.provenance_model import ProvenanceRecord

from pydash.arrays import compact


class PatternMatcher:
    def __init__(
        self,
        query: Dict,
        provenance_service: ProvenanceService,
        user_scopes: Sequence[Scope] = (),
    ):
        self._query = query
        self._scopes = user_scopes
        self._provenance_service = provenance_service

        self._lemma_matcher = (
            LemmaMatcher(
                query["lemmas"],
                query.get("lemmaOperator", LemmaQueryType.AND),
            )
            if "lemmas" in query
            else EmptyMatcher()
        )

        self._sign_matcher = (
            SignMatcher(query["transliteration"])
            if "transliteration" in query
            else EmptyMatcher()
        )

    def _sort_by(self, sort_fields: Optional[Dict] = None) -> List[Dict]:
        return [{"$sort": sort_fields}] if sort_fields else []

    def _filter_by_script(self) -> Dict:
        parameters = {
            "scriptPeriod": "script.period",
            "scriptPeriodModifier": "script.periodModifier",
        }

        return {
            path: self._query.get(parameter)
            for parameter, path in parameters.items()
            if self._query.get(parameter)
        }

    def _filter_by_genre(self) -> Dict:
        if genre := self._query.get("genre"):
            return {"genres.category": {"$all": genre}}
        return {}

    def _filter_by_museum(self) -> Dict:
        return {"museum": museum} if (museum := self._query.get("museum")) else {}

    def _filter_by_project(self) -> Dict:
        return {"projects": project} if (project := self._query.get("project")) else {}

    def _filter_by_site(self) -> Dict:
        if provenance := self._query.get("site"):
            record = self._lookup_provenance_record(provenance)
            if record is None:
                return {"archaeology.site": provenance}
            if record.parent is None:
                return {"archaeology.site": record.long_name}
            children = [
                child.long_name
                for child in self._provenance_service.find_children(record.long_name)
            ]
            if children:
                return {"archaeology.site": {"$in": [record.long_name] + children}}
            return {"archaeology.site": record.long_name}
        return {}

    def _lookup_provenance_record(self, provenance: str) -> Optional[ProvenanceRecord]:
        record = self._provenance_service.find_by_name(provenance)
        if record is not None:
            return record
        record = self._provenance_service.find_by_id(provenance.upper())
        if record is not None:
            return record
        return None

    def _filter_by_reference(self) -> Dict:
        if "bibId" not in self._query:
            return {}

        parameters = {"id": self._query["bibId"]}
        if "pages" in self._query:
            parameters["pages"] = {
                "$regex": rf".*?(^|[^\d]){self._query['pages']}([^\d]|$).*?"
            }
        return {"references": {"$elemMatch": parameters}}

    def _filter_by_dossier(self) -> Dict:
        return (
            {"dossiers.dossierId": dossier}
            if (dossier := self._query.get("dossier"))
            else {}
        )

    def _prefilter(self) -> List[Dict]:
        constraints = {
            "$and": compact(
                [
                    number_is(self._query["number"]) if "number" in self._query else {},
                    self._filter_by_genre(),
                    self._filter_by_museum(),
                    self._filter_by_project(),
                    self._filter_by_site(),
                    self._filter_by_script(),
                    self._filter_by_reference(),
                    self._filter_by_dossier(),
                    match_user_scopes(self._scopes),
                ]
            ),
        }

        return [{"$match": constraints}] if constraints else []

    def _default_pipeline(self) -> List[Dict]:
        return [
            {
                "$project": {
                    "_id": True,
                    "museumNumber": True,
                    "matchingLines": {"$literal": []},
                    "matchCount": {"$literal": 0},
                    "_sortKey": True,
                    "_scriptSortKey": "$script.sortKey",
                }
            },
        ]

    def _merge_pipelines(self) -> List[Dict]:
        return [
            {
                "$facet": {
                    "transliteration": self._sign_matcher.build_pipeline(
                        count_matches_per_item=False
                    ),
                    "lemmas": self._lemma_matcher.build_pipeline(
                        count_matches_per_item=False
                    ),
                }
            },
            {
                "$project": {
                    "combined": {"$concatArrays": ["$transliteration", "$lemmas"]}
                }
            },
            {"$unwind": "$combined"},
            {"$replaceRoot": {"newRoot": "$combined"}},
            {
                "$group": {
                    "_id": "$_id",
                    "matchingLines": {"$push": "$matchingLines"},
                    "museumNumber": {"$first": "$museumNumber"},
                    "_sortKey": {"$first": "$_sortKey"},
                    "_scriptSortKey": {"$first": "$_scriptSortKey"},
                },
            },
            {
                "$match": {
                    "matchingLines": {"$size": 2},
                }
            },
            {
                "$addFields": {
                    "matchingLines": {
                        "$setUnion": [
                            {"$arrayElemAt": ["$matchingLines", 0]},
                            {"$arrayElemAt": ["$matchingLines", 1]},
                        ]
                    }
                }
            },
            {"$addFields": {"matchCount": {"$size": "$matchingLines"}}},
            {"$match": {"matchCount": {"$gt": 0}}},
        ]

    def _get_pipeline_components(self) -> List[Dict]:
        dispatcher = {
            (True, True): self._merge_pipelines,
            (True, False): self._lemma_matcher.build_pipeline,
            (False, True): self._sign_matcher.build_pipeline,
            (False, False): self._default_pipeline,
        }
        key = (
            isinstance(self._lemma_matcher, LemmaMatcher),
            isinstance(self._sign_matcher, SignMatcher),
        )

        facet = {
            "items": [
                *self._sort_by({"_scriptSortKey": 1, "_sortKey": 1}),
                *items_pipeline(self._query),
            ],
        }
        if count_is_exact(self._query):
            facet["count"] = count_pipeline()

        return [
            *self._prefilter(),
            *dispatcher[key](),
            {"$facet": facet},
            {"$project": result_projection(self._query)},
        ]

    def build_pipeline(self) -> List[Dict]:
        return self._get_pipeline_components()
