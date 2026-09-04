from itertools import islice
from typing import Any, Dict, List, Sequence, Tuple, cast

from ebl.transliteration.application.one_of_line_schema import OneOfLineSchema
from ebl.transliteration.domain.atf import DEFAULT_ATF_PARSER_VERSION
from ebl.transliteration.domain.text import Text

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
    # Production hydration path. Output is fed through schema load, so the
    # key is the wire name ``parserVersion``.
    return {
        "lines": [
            preview_line_of(index, line)
            for index, line in selected_lines(text.get("lines") or [], matching_lines)
        ],
        "parserVersion": text.get("parser_version") or DEFAULT_ATF_PARSER_VERSION,
    }


def matching_line_preview_of(
    text: Text, matching_lines: Sequence[int]
) -> Dict[str, Any]:
    # Domain-Text builder, currently exercised only by tests. Output goes
    # straight onto the domain object, so the key is the attribute name
    # ``parser_version``.
    schema = OneOfLineSchema()
    return {
        "lines": [
            preview_line_of(index, cast(dict, schema.dump(line)))
            for index, line in selected_lines(text.lines, matching_lines)
        ],
        "parser_version": text.parser_version or DEFAULT_ATF_PARSER_VERSION,
    }
