from typing import List, Mapping, Sequence, cast

from ebl.corpus.application.lines_pagination import MAX_LINES_OFFSET
from ebl.corpus.application.outline_schemas import load_chapter_outline
from ebl.corpus.application.schemas import LineSchema
from ebl.corpus.domain.chapter import ChapterId
from ebl.corpus.domain.chapter_outline import ChapterOutline
from ebl.corpus.domain.line import Line
from ebl.corpus.domain.lines_page import LinesPage
from ebl.corpus.infrastructure.mongo_text_repository_base import (
    MongoTextRepositoryBase,
    chapter_not_found,
)
from ebl.corpus.infrastructure.queries import chapter_id_query

OUTLINE_CHAPTER_FIELDS: Sequence[str] = (
    "textId",
    "classification",
    "stage",
    "version",
    "name",
    "order",
    "uncertainFragments",
)
OUTLINE_MANUSCRIPT_FIELDS: Sequence[str] = (
    "id",
    "siglumDisambiguator",
    "museumNumber",
    "accession",
    "periodModifier",
    "period",
    "provenance",
    "type",
    "notes",
    "references",
)
OUTLINE_LINE_FIELDS: Sequence[str] = (
    "number",
    "isSecondLineOfParallelism",
    "isBeginningOfSection",
    "translation",
)
OUTLINE_VARIANT_FIELDS: Sequence[str] = ("reconstruction", "note", "parallelLines")


def _pick_fields(variable: str, fields: Sequence[str]) -> dict:
    return {field: f"$${variable}.{field}" for field in fields}


def _map(input_: str, variable: str, projection: Mapping[str, object]) -> dict:
    return {"$map": {"input": input_, "as": variable, "in": dict(projection)}}


def _project_outline_variants() -> dict:
    return _map(
        "$$line.variants",
        "variant",
        {
            **_pick_fields("variant", OUTLINE_VARIANT_FIELDS),
            "manuscriptIds": "$$variant.manuscripts.manuscriptId",
        },
    )


def _project_outline_lines() -> dict:
    return _map(
        "$lines",
        "line",
        {
            **_pick_fields("line", OUTLINE_LINE_FIELDS),
            "variants": _project_outline_variants(),
        },
    )


def aggregate_chapter_outline(id_: ChapterId) -> List[dict]:
    return [
        {"$match": chapter_id_query(id_)},
        {
            "$project": {
                "_id": False,
                **dict.fromkeys(OUTLINE_CHAPTER_FIELDS, True),
                "manuscripts": _map(
                    "$manuscripts",
                    "manuscript",
                    _pick_fields("manuscript", OUTLINE_MANUSCRIPT_FIELDS),
                ),
                "lines": _project_outline_lines(),
            }
        },
    ]


def _validate_lines_slice(offset: int, limit: int) -> None:
    if not 0 <= offset <= MAX_LINES_OFFSET:
        raise ValueError(
            f"offset must be between 0 and {MAX_LINES_OFFSET}, got {offset} instead"
        )
    if limit < 1:
        raise ValueError(f"limit must be at least 1, got {limit} instead")


def aggregate_lines_page(id_: ChapterId, offset: int, limit: int) -> List[dict]:
    _validate_lines_slice(offset, limit)
    return [
        {"$match": chapter_id_query(id_)},
        {
            "$project": {
                "_id": False,
                "total": {"$size": "$lines"},
                "lines": {"$slice": ["$lines", offset, limit]},
            }
        },
    ]


class MongoTextRepositoryOutline(MongoTextRepositoryBase):
    def _aggregate_chapter(self, id_: ChapterId, pipeline: List[dict]) -> dict:
        try:
            return cast(dict, next(self._chapters.aggregate(pipeline)))
        except StopIteration as error:
            raise chapter_not_found(id_) from error

    def find_chapter_outline(self, id_: ChapterId) -> ChapterOutline:
        return load_chapter_outline(
            self._aggregate_chapter(id_, aggregate_chapter_outline(id_)),
            self._provenance_service,
        )

    def find_lines_page(self, id_: ChapterId, offset: int, limit: int) -> LinesPage:
        document = self._aggregate_chapter(
            id_, aggregate_lines_page(id_, offset, limit)
        )
        lines = cast(Sequence[Line], LineSchema().load(document["lines"], many=True))
        return LinesPage(document["total"], offset, limit, tuple(lines))
