from typing import Any, Dict, Iterator, Optional, Sequence, Union, cast

from ebl.errors import NotFoundError
from ebl.fragmentarium.application.fragment_query_preview import (
    matching_line_preview_of_data,
)
from ebl.fragmentarium.application.fragment_query_summary_schema import (
    FragmentQueryResultSchema,
)
from ebl.fragmentarium.domain.fragment_query_summary import FragmentQueryResult
from ebl.fragmentarium.infrastructure.mongo_fragment_repository_base import (
    MongoFragmentRepositoryBase,
)
from ebl.common.query.query_result import QueryResult
from ebl.common.query.query_schemas import QueryResultSchema
from ebl.transliteration.application.museum_number_schema import (
    MuseumNumberSchema,
)
from ebl.transliteration.domain.museum_number import MuseumNumber

FRAGMENT_QUERY_SUMMARY_PROJECTION = {
    "_id": True,
    "accession": True,
    "archaeology.excavationNumber": True,
    "archaeology.site": True,
    "date": True,
    "description": True,
    "dossiers": True,
    "genres": True,
    "museumNumber": True,
    "projects": True,
    "references": True,
    "script": True,
    "text.lines": True,
    "text.parser_version": True,
}


def fragment_photo_filename(museum_number: Union[dict, MuseumNumber]) -> str:
    if isinstance(museum_number, MuseumNumber):
        return f"{museum_number}.jpg"

    suffix = museum_number.get("suffix") or ""
    suffix_part = f".{suffix}" if suffix else ""
    return f"{museum_number.get('prefix', '')}.{museum_number.get('number', '')}{suffix_part}.jpg"


def load_museum_number(data: dict) -> MuseumNumber:
    return cast(MuseumNumber, MuseumNumberSchema().load(data.get("museumNumber", data)))


def load_query_result(cursor: Iterator) -> QueryResult:
    data = next(cursor, None)
    return (
        cast(QueryResult, QueryResultSchema().load(data))
        if data
        else QueryResult.create_empty()
    )


class MongoFragmentRepositoryGetSummary(MongoFragmentRepositoryBase):
    def _find_fragment_query_summary_data(
        self, fragment_ids: Sequence[Any]
    ) -> Dict[Any, dict]:
        return {
            fragment["_id"]: fragment
            for fragment in self._fragments.find_many(
                {"_id": {"$in": list(fragment_ids)}},
                projection=FRAGMENT_QUERY_SUMMARY_PROJECTION,
            )
        }

    def _find_fragment_query_photo_filenames(
        self, items: Sequence[dict]
    ) -> Sequence[str]:
        filenames = [
            fragment_photo_filename(item["museumNumber"])
            for item in items
            if item.get("museumNumber")
        ]
        return [
            photo["filename"]
            for photo in self._photo_files.find_many(
                {"filename": {"$in": filenames}},
                projection={"filename": True},
            )
        ]

    def _hydrate_fragment_query_item(
        self,
        item: dict,
        fragments_by_id: Dict[Any, dict],
        photo_filenames: Sequence[str],
    ) -> dict:
        fragment = fragments_by_id.get(item["_id"])
        if fragment is None:
            raise NotFoundError(
                f"Fragment summary data for {item.get('museumNumber')} not found."
            )

        matching_lines = item.get("matchingLines") or []
        museum_number = fragment.get("museumNumber") or item["museumNumber"]
        return {
            "museumNumber": museum_number,
            "accession": fragment.get("accession"),
            "description": fragment.get("description", ""),
            "script": fragment.get(
                "script",
                {"period": "", "periodModifier": "None", "uncertain": False},
            ),
            "date": fragment.get("date"),
            "genres": fragment.get("genres", []),
            "archaeology": fragment.get("archaeology"),
            "references": fragment.get("references", []),
            "projects": fragment.get("projects", []),
            "dossiers": fragment.get("dossiers", []),
            "matchingLines": matching_lines,
            "matchingLinePreview": matching_line_preview_of_data(
                fragment.get("text") or {}, matching_lines
            ),
            "matchCount": item.get("matchCount", 0),
            "hasPhoto": fragment_photo_filename(museum_number) in photo_filenames,
        }

    def _load_fragment_query_result(self, data: Optional[dict]) -> FragmentQueryResult:
        if not data:
            return FragmentQueryResult.create_empty()

        items = data.get("items", [])
        fragment_ids = [item["_id"] for item in items]
        fragments_by_id = self._find_fragment_query_summary_data(fragment_ids)
        photo_filenames = self._find_fragment_query_photo_filenames(items)
        return cast(
            FragmentQueryResult,
            FragmentQueryResultSchema().load(
                {
                    "items": [
                        self._hydrate_fragment_query_item(
                            item, fragments_by_id, photo_filenames
                        )
                        for item in items
                    ],
                    "matchCountTotal": data.get("matchCountTotal", 0),
                    "isMatchCountTotalExact": data.get("isMatchCountTotalExact", True),
                    "hasNextPage": data.get("hasNextPage"),
                }
            ),
        )
