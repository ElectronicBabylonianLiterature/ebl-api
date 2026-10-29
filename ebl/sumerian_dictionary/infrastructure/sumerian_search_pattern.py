import re
from typing import Dict, Mapping, Sequence

from ebl.common.query.query_collation import CollatedFieldQuery, DataType, Fields
from ebl.sumerian_dictionary.infrastructure.sumerian_search_ranking import fold

DATA_TYPE: DataType = "sumerian-dictionary"
SEARCHED_FIELDS: Sequence[str] = Fields.SUMERIAN_DICTIONARY.value["COLLATED_FIELDS"]
IGNORABLE_CHARACTERS = "[{}̀-ͯ]*"
PRECOMPOSED_LATIN_RANGES: Sequence[range] = (
    range(0x00C0, 0x0250),
    range(0x1E00, 0x1F00),
)


def _letters_by_fold() -> Mapping[str, str]:
    letters: Dict[str, str] = {}
    for code_range in PRECOMPOSED_LATIN_RANGES:
        for letter in map(chr, code_range):
            folded = fold(letter)
            if len(folded) == 1 and folded != letter:
                letters[folded] = letters.get(folded, "") + letter
    return letters


LETTERS_BY_FOLD = _letters_by_fold()


def _class_members(pattern: str) -> str:
    return pattern[1:-1] if pattern.startswith("[") else pattern


def _character_pattern(character: str) -> str:
    collated = CollatedFieldQuery(character, SEARCHED_FIELDS[0], DATA_TYPE).value
    pattern = collated or re.escape(character)
    letters = LETTERS_BY_FOLD.get(character)
    if not letters:
        return pattern
    members = dict.fromkeys(_class_members(pattern) + letters)
    return f"[{''.join(members)}]"


def search_pattern(folded_query: str) -> str:
    return IGNORABLE_CHARACTERS.join(
        _character_pattern(character) for character in folded_query
    )
