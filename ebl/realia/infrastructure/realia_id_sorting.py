import unicodedata
from typing import Iterable, List, Tuple


def sort_realia_ids(identifiers: Iterable[str]) -> List[str]:
    return sorted(identifiers, key=_sort_key)


def _sort_key(identifier: str) -> Tuple[str, str]:
    return (_strip_accents_and_case(identifier), identifier)


def _strip_accents_and_case(identifier: str) -> str:
    decomposed = unicodedata.normalize("NFKD", identifier)
    return "".join(
        character for character in decomposed if not unicodedata.combining(character)
    ).casefold()
