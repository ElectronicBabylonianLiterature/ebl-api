from typing import Any, Dict, Sequence, cast

from ebl.fragmentarium.application.fragment_query_preview import (
    matching_line_preview_of_data,
)
from ebl.fragmentarium.application.fragment_query_summary_schema import (
    FragmentQueryMatchingLinePreviewSchema,
)
from ebl.transliteration.application.one_of_line_schema import OneOfLineSchema
from ebl.transliteration.application.text_schema import TextSchema
from ebl.transliteration.domain.text import Text

COMPLEX_ATF = "1'. [ku]-nu-uš KUR# {d}INANA ⸢ki⸣ %sux gu-du/gu₂"
PREVIEW_LINE_FIELDS = {"index", "type", "prefix", "content", "lineNumber"}


def dumped(line) -> dict:
    return cast(dict, OneOfLineSchema().dump(line))


def dumped_text(text: Text) -> dict:
    return cast(dict, TextSchema().dump(text))


def numbered_atf(count: int, word: str = "ku-nu-uš") -> str:
    return "\n".join(f"{index}. {word}" for index in range(1, count + 1))


def matching_line_preview_of(
    text: Text, matching_lines: Sequence[int]
) -> Dict[str, Any]:
    return cast(
        Dict[str, Any],
        FragmentQueryMatchingLinePreviewSchema().load(
            matching_line_preview_of_data(dumped_text(text), matching_lines)
        ),
    )
