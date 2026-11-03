from itertools import islice
from typing import Any, Dict, List, Sequence, Tuple, cast

from marshmallow import EXCLUDE

from ebl.transliteration.application.one_of_line_schema import OneOfLineSchema
from ebl.transliteration.domain.atf import DEFAULT_ATF_PARSER_VERSION

MAX_PREVIEW_LINES = 5


def is_text_line(line: dict) -> bool:
    return line.get("type") == "TextLine"


def api_line_of(stored_line: dict) -> Dict[str, Any]:
    schema = OneOfLineSchema()
    return cast(Dict[str, Any], schema.dump(schema.load(stored_line, unknown=EXCLUDE)))


def preview_line_of(index: int, line: dict) -> Dict[str, Any]:
    return {**api_line_of(line), "index": index}


def selected_lines(
    lines: Sequence[dict], matching_lines: Sequence[int]
) -> List[Tuple[int, dict]]:
    unique_indices = dict.fromkeys(
        index
        for index in matching_lines
        if 0 <= index < len(lines) and is_text_line(lines[index])
    )
    return [
        (index, lines[index]) for index in islice(unique_indices, MAX_PREVIEW_LINES)
    ]


def matching_line_preview_of_data(
    text: dict, matching_lines: Sequence[int]
) -> Dict[str, Any]:
    return {
        "lines": [
            preview_line_of(index, line)
            for index, line in selected_lines(text.get("lines") or [], matching_lines)
        ],
        "parserVersion": text.get("parser_version") or DEFAULT_ATF_PARSER_VERSION,
    }
