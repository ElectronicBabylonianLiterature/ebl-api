from typing import List, Mapping, Sequence, cast

from marshmallow import Schema

from ebl.corpus.application.schemas import ChapterSchema, LineSchema
from ebl.corpus.domain.chapter import Chapter
from ebl.corpus.domain.chapter_change import (
    CHAPTER_FIELDS,
    LINES_FIELD,
    KeptContent,
    LineRun,
)
from ebl.corpus.domain.line import Line
from ebl.corpus.infrastructure.mongo_text_repository_base import REVISION_FIELD
from ebl.transliteration.application.storage_serialization import (
    storage_serialization,
)

STORED_LINES = f"${LINES_FIELD}"


def create_literal(value: object) -> dict:
    return {"$literal": value}


def _create_stored_lines(run: LineRun) -> dict:
    return {"$slice": [STORED_LINES, run.source, run.count]}


def _dump(schema: Schema, value: object) -> object:
    with storage_serialization():
        return schema.dump(value)


def _create_dumped_lines(lines: Sequence[Line]) -> List[dict]:
    return [create_literal(_dump(LineSchema(many=True), lines))] if lines else []


def _take_lines(lines: Sequence[Line], start: int, end: int) -> Sequence[Line]:
    if not start <= end <= len(lines):
        raise ValueError(
            f"Lines {start} to {end} are not a part of {len(lines)} lines."
        )
    return lines[start:end]


def create_lines_expression(lines: Sequence[Line], runs: Sequence[LineRun]) -> dict:
    segments: List[dict] = []
    position = 0
    for run in runs:
        segments.extend(_create_dumped_lines(_take_lines(lines, position, run.target)))
        segments.append(_create_stored_lines(run))
        position = run.target + run.count
    segments.extend(_create_dumped_lines(_take_lines(lines, position, len(lines))))
    return {"$concatArrays": segments} if segments else create_literal([])


def _dump_fields(chapter: Chapter, fields: Sequence[str]) -> dict:
    return cast(dict, _dump(ChapterSchema(only=fields), chapter)) if fields else {}


def create_chapter_update(
    chapter: Chapter, kept: KeptContent, revision: str
) -> List[dict]:
    fields = [field for field in CHAPTER_FIELDS if field not in kept.fields]
    lines = (
        {}
        if LINES_FIELD in kept.fields
        else {LINES_FIELD: create_lines_expression(chapter.lines, kept.line_runs)}
    )
    dumped_fields = _dump_fields(chapter, fields)
    return [
        {
            "$set": {
                **lines,
                **{key: create_literal(value) for key, value in dumped_fields.items()},
                REVISION_FIELD: create_literal(revision),
            }
        }
    ]


def _create_line_path(position: int) -> str:
    if position < 0:
        raise ValueError(f"Invalid line position: {position}.")
    return f"{LINES_FIELD}.{position}"


def create_lines_update(lines: Mapping[int, Line], revision: str) -> dict:
    return {
        "$set": {
            **{
                _create_line_path(position): _dump(LineSchema(), line)
                for position, line in lines.items()
            },
            REVISION_FIELD: revision,
        }
    }
