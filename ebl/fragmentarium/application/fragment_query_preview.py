from itertools import islice
from typing import Any, Dict, List, Sequence, cast

from ebl.transliteration.application.one_of_line_schema import OneOfLineSchema
from ebl.transliteration.domain.atf import DEFAULT_ATF_PARSER_VERSION
from ebl.transliteration.domain.text import Text

MAX_PREVIEW_LINES = 5


def preview_token_of(token: dict) -> Dict[str, Any]:
    data = {
        "value": token.get("value"),
        "cleanValue": token.get("cleanValue"),
        "uniqueLemma": token.get("uniqueLemma"),
        "type": token.get("type"),
    }
    return {
        key: value
        for key, value in data.items()
        if value is not None and (key != "uniqueLemma" or value)
    }


def preview_line_of(line: dict) -> Dict[str, Any]:
    content = line.get("content") or []
    prefix = line.get("prefix") or ""
    data = {
        "type": line.get("type"),
        "number": prefix,
        "prefix": prefix,
        "text": " ".join(token.get("value", "") for token in content),
        "tokens": [preview_token_of(token) for token in content],
        "lineNumber": line.get("lineNumber"),
        "content": content,
    }
    return {key: value for key, value in data.items() if value is not None}


def selected_lines(lines: Sequence, matching_lines: Sequence[int]) -> List:
    return list(
        islice(
            (lines[index] for index in matching_lines if 0 <= index < len(lines)),
            MAX_PREVIEW_LINES,
        )
    )


def matching_line_preview_of_data(
    text: dict, matching_lines: Sequence[int]
) -> Dict[str, Any]:
    return {
        "lines": [
            preview_line_of(line)
            for line in selected_lines(text.get("lines") or [], matching_lines)
        ],
        "parserVersion": text.get("parser_version") or DEFAULT_ATF_PARSER_VERSION,
    }


def matching_line_preview_of(
    text: Text, matching_lines: Sequence[int]
) -> Dict[str, Any]:
    schema = OneOfLineSchema()
    return {
        "lines": [
            preview_line_of(cast(dict, schema.dump(line)))
            for line in selected_lines(text.lines, matching_lines)
        ],
        "parserVersion": text.parser_version or DEFAULT_ATF_PARSER_VERSION,
    }
