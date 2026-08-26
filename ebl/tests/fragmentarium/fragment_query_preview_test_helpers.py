from typing import cast

from ebl.fragmentarium.application.fragment_schema import FragmentSchema
from ebl.transliteration.application.one_of_line_schema import OneOfLineSchema

COMPLEX_ATF = "1'. [ku]-nu-uš KUR# {d}INANA ⸢ki⸣ %sux gu-du/gu₂"
PREVIEW_LINE_FIELDS = {"index", "number", "prefix", "text", "tokens"}


def dumped(line) -> dict:
    return cast(dict, OneOfLineSchema().dump(line))


def dumped_text(fragment) -> dict:
    return cast(dict, FragmentSchema(exclude=["joins"]).dump(fragment))["text"]


def numbered_atf(count: int, word: str = "ku-nu-uš") -> str:
    return "\n".join(f"{index}. {word}" for index in range(1, count + 1))
