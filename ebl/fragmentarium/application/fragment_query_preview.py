from itertools import islice
from typing import Any, Dict, List, Sequence, Tuple

from ebl.transliteration.domain.atf import DEFAULT_ATF_PARSER_VERSION

MAX_PREVIEW_LINES = 5


def is_text_line(line: Any) -> bool:
    type_name = line.get("type") if isinstance(line, dict) else type(line).__name__
    return type_name == "TextLine"


def preview_line_of(index: int, line: dict) -> Dict[str, Any]:
    return {**line, "index": index}


def selected_lines(
    lines: Sequence, matching_lines: Sequence[int]
) -> List[Tuple[int, Any]]:
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
