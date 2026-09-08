from typing import Any, Dict, Sequence, cast

from ebl.fragmentarium.application.fragment_query_preview import (
    preview_line_of,
    selected_lines,
)
from ebl.fragmentarium.application.fragment_schema import FragmentSchema
from ebl.transliteration.application.one_of_line_schema import OneOfLineSchema
from ebl.transliteration.domain.atf import DEFAULT_ATF_PARSER_VERSION
from ebl.transliteration.domain.text import Text

COMPLEX_ATF = "1'. [ku]-nu-uš KUR# {d}INANA ⸢ki⸣ %sux gu-du/gu₂"
PREVIEW_LINE_FIELDS = {"index", "type", "prefix", "content", "lineNumber"}


def dumped(line) -> dict:
    return cast(dict, OneOfLineSchema().dump(line))


def dumped_text(fragment) -> dict:
    return cast(dict, FragmentSchema(exclude=["joins"]).dump(fragment))["text"]


def numbered_atf(count: int, word: str = "ku-nu-uš") -> str:
    return "\n".join(f"{index}. {word}" for index in range(1, count + 1))


def matching_line_preview_of(
    text: Text, matching_lines: Sequence[int]
) -> Dict[str, Any]:
    schema = OneOfLineSchema()
    return {
        "lines": [
            preview_line_of(index, cast(dict, schema.dump(line)))
            for index, line in selected_lines(text.lines, matching_lines)
        ],
        "parser_version": text.parser_version or DEFAULT_ATF_PARSER_VERSION,
    }
