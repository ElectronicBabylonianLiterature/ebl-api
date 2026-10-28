import re
import unicodedata
from enum import IntEnum
from typing import Callable, Mapping, Optional, Sequence, Tuple

ROMAN_NUMERALS: Sequence[str] = (
    "I",
    "II",
    "III",
    "IV",
    "V",
    "VI",
    "VII",
    "VIII",
    "IX",
    "X",
)
DIGRAPHS: Sequence[Tuple[str, str]] = (
    ("ŋ", "ĝ"),
    ("sz", "š"),
    ("s,", "ṣ"),
    ("t,", "ṭ"),
)
SUBSCRIPTS = str.maketrans("₀₁₂₃₄₅₆₇₈₉ₓ", "0123456789x")
COMBINING_MARKS = re.compile("[̀-ͯ]")
BRACES = re.compile("[{}]")
TEXT_SEPARATOR = " | "


class MatchRank(IntEnum):
    CITATION_FORM_AS_TYPED = 0
    CITATION_FORM_FOLDED = 1
    ALIAS = 2
    GUIDE_WORD = 3
    CITATION_FORM_PREFIX = 4
    CITATION_FORM_SUBSTRING = 5
    WHOLE_WORD_IN_TEXT = 6
    SUBSTRING_IN_TEXT = 7


RankCheck = Tuple[MatchRank, Callable[[], bool]]


def fold(value: str) -> str:
    lowered = value.lower()
    for digraph, replacement in DIGRAPHS:
        lowered = lowered.replace(digraph, replacement)
    decomposed = unicodedata.normalize("NFD", lowered)
    return COMBINING_MARKS.sub("", decomposed).translate(SUBSCRIPTS)


def _strings(document: Mapping[str, object], key: str) -> Sequence[str]:
    value = document.get(key)
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str)]


def _string(document: Mapping[str, object], key: str) -> str:
    value = document.get(key)
    return value if isinstance(value, str) else ""


def _count(document: Mapping[str, object], key: str) -> int:
    value = document.get(key)
    return value if isinstance(value, int) else 0


def _homonym_order(homonym: str) -> int:
    return ROMAN_NUMERALS.index(homonym) if homonym in ROMAN_NUMERALS else -1


class SumerianRelevanceRanker:
    def __init__(self, query: str) -> None:
        self._raw = query.strip().lower()
        self._folded = fold(self._raw)
        self._whole_word = re.compile(f"(^|[^a-z]){re.escape(self._folded)}([^a-z]|$)")

    @property
    def folded_query(self) -> str:
        return self._folded

    def alias_hit(self, document: Mapping[str, object]) -> str:
        if fold(_string(document, "citationForm")) == self._folded:
            return ""
        for form in _strings(document, "aliasForms"):
            folded_form = fold(form)
            if self._folded in (folded_form, BRACES.sub("", folded_form)):
                return form
        return ""

    def rank(self, document: Mapping[str, object]) -> Optional[MatchRank]:
        return next(
            (rank for rank, matches in self._checks(document) if matches()), None
        )

    def _checks(self, document: Mapping[str, object]) -> Sequence[RankCheck]:
        citation_form = _string(document, "citationForm")
        folded_form = fold(citation_form)
        guide_word = fold(_string(document, "guideWord"))
        text = fold(
            TEXT_SEPARATOR.join(
                [
                    *_strings(document, "senseMeanings"),
                    *_strings(document, "akkadianWordIds"),
                ]
            )
        )
        query = self._folded
        return (
            (
                MatchRank.CITATION_FORM_AS_TYPED,
                lambda: citation_form.lower() == self._raw,
            ),
            (MatchRank.CITATION_FORM_FOLDED, lambda: folded_form == query),
            (MatchRank.ALIAS, lambda: bool(self.alias_hit(document))),
            (MatchRank.GUIDE_WORD, lambda: guide_word == query),
            (MatchRank.CITATION_FORM_PREFIX, lambda: folded_form.startswith(query)),
            (MatchRank.CITATION_FORM_SUBSTRING, lambda: query in folded_form),
            (
                MatchRank.WHOLE_WORD_IN_TEXT,
                lambda: bool(self._whole_word.search(f"{guide_word} {text}")),
            ),
            (MatchRank.SUBSTRING_IN_TEXT, lambda: query in text),
        )

    def key(
        self, rank: MatchRank, document: Mapping[str, object]
    ) -> Tuple[int, int, int, int, int, str]:
        return (
            rank,
            0 if document.get("hasAttinger") is True else 1,
            -_count(document, "attestationCount"),
            len(_string(document, "citationForm")),
            _homonym_order(_string(document, "homonym")),
            _string(document, "_id"),
        )
