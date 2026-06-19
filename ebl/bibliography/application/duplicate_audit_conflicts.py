from __future__ import annotations

import re
from typing import Mapping, Optional, Sequence

from ebl.bibliography.application.duplicate_audit_normalization import (
    NormalizedBibliographyEntry,
)
from ebl.bibliography.application.duplicate_audit_similarity import pair_type, ratio

SERIES_NUMBER_WORDS = {
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "first": 1,
    "second": 2,
    "third": 3,
    "fourth": 4,
    "fifth": 5,
    "sixth": 6,
    "seventh": 7,
    "eighth": 8,
    "ninth": 9,
    "tenth": 10,
}
_URL_PATTERN = re.compile(r"https?://\S+", re.IGNORECASE)


def conflicting_signals(matched: Mapping[str, Optional[float]]) -> list[str]:
    return [
        signal
        for signal in ("doi", "isbn", "year", "volume", "issue", "page", "edition")
        if matched.get(signal) == 0.0
    ]


def calibrated_conflicting_signals(
    left: NormalizedBibliographyEntry,
    right: NormalizedBibliographyEntry,
    matched: Mapping[str, Optional[float]],
) -> list[str]:
    conflicts = conflicting_signals(matched)
    conflicts.extend(
        name
        for signal, name in (
            ("volume", "different_volume"),
            ("issue", "different_issue"),
            ("page", "different_page"),
        )
        if signal in conflicts
    )
    checks = (
        ("different_title", is_different_main_title(matched)),
        ("different_contributors", is_different_contributors(matched)),
        ("series_part", is_series_part_sibling(left, right)),
        ("different_entry_title", is_different_entry_title(left, right, matched)),
        ("different_webpage_title", is_different_webpage_title(left, right, matched)),
        ("series_part", is_complete_incomplete_variant(left, right, matched)),
    )
    conflicts.extend(name for name, applies in checks if applies)
    if is_doi_data_issue(matched, conflicts):
        conflicts.append("doi_data_issue")
    return unique_in_order(conflicts)


def unique_in_order(values: Sequence[str]) -> list[str]:
    return sorted(set(values), key=values.index)


def is_different_main_title(matched: Mapping[str, Optional[float]]) -> bool:
    title_score = matched.get("title")
    return title_score is not None and title_score < 0.65


def is_different_contributors(matched: Mapping[str, Optional[float]]) -> bool:
    contributor_score = matched.get("contributors")
    return contributor_score is not None and contributor_score < 0.4


def is_different_entry_title(
    left: NormalizedBibliographyEntry,
    right: NormalizedBibliographyEntry,
    matched: Mapping[str, Optional[float]],
) -> bool:
    if pair_type(left, right) != "entry-encyclopedia":
        return False
    title_score = matched.get("title")
    return title_score is not None and title_score < 0.92


def is_doi_data_issue(
    matched: Mapping[str, Optional[float]], conflicts: Sequence[str]
) -> bool:
    if matched.get("doi") != 1.0:
        return False
    metadata_conflicts = {
        "year",
        "different_page",
        "different_volume",
        "different_issue",
        "different_entry_title",
        "different_title",
        "different_contributors",
        "different_webpage_title",
        "series_part",
    }
    if metadata_conflicts.intersection(conflicts):
        return True
    title_score = matched.get("title")
    return title_score is not None and title_score < 0.85


def is_series_part_sibling(
    left: NormalizedBibliographyEntry, right: NormalizedBibliographyEntry
) -> bool:
    left_part = series_part(left.title)
    right_part = series_part(right.title)
    if left_part and right_part:
        return are_distinct_matching_parts(left_part, right_part)
    if left_part:
        return _is_stem_match(left_part[0], right.title)
    if right_part:
        return _is_stem_match(right_part[0], left.title)
    return False


def are_distinct_matching_parts(
    left_part: tuple[str, int], right_part: tuple[str, int]
) -> bool:
    left_stem, left_number = left_part
    right_stem, right_number = right_part
    stem_ratio = ratio(left_stem, right_stem) or 0.0
    return left_number != right_number and stem_ratio >= 0.9


def _is_stem_match(stem: str, title: str) -> bool:
    stem_ratio = ratio(stem, title)
    return stem_ratio is not None and stem_ratio >= 0.95


def is_different_webpage_title(
    left: NormalizedBibliographyEntry,
    right: NormalizedBibliographyEntry,
    matched: Mapping[str, Optional[float]],
) -> bool:
    if pair_type(left, right) != "webpage":
        return False
    title_score = matched.get("title")
    if title_score is not None and title_score < 0.93:
        return True
    left_url = _extract_url(str(left.raw.get("title") or ""))
    right_url = _extract_url(str(right.raw.get("title") or ""))
    return bool(left_url and right_url and left_url != right_url)


def _extract_url(title: str) -> str:
    match = _URL_PATTERN.search(title)
    return match.group(0).rstrip(").") if match else ""


def is_complete_incomplete_variant(
    left: NormalizedBibliographyEntry,
    right: NormalizedBibliographyEntry,
    matched: Mapping[str, Optional[float]],
) -> bool:
    title_score = matched.get("title")
    if title_score is not None and title_score < 0.97:
        return False
    complete_pattern = re.compile(r"\bcomplete\s+dates\b", re.IGNORECASE)
    incomplete_pattern = re.compile(r"\bincomplete\s+dates\b", re.IGNORECASE)
    has_complete = bool(
        complete_pattern.search(left.title) or complete_pattern.search(right.title)
    )
    has_incomplete = bool(
        incomplete_pattern.search(left.title) or incomplete_pattern.search(right.title)
    )
    return has_complete and has_incomplete


def series_part(title: str) -> Optional[tuple[str, int]]:
    patterns = (
        r"^(.+)\b(?:part|volume|vol|band|teil|heft|tome)\s+([ivxlcdm]+|\d+|one|two|three|four|five|six|seven|eight|nine|ten|first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth)\b.*$",
        r"^(.+\b\w+)\s+([ivxlcdm]+|\d+)$",
    )
    for pattern in patterns:
        if match := re.match(pattern, title):
            stem = re.sub(r"\s+", " ", match[1]).strip()
            number = parse_series_number(match[2])
            if stem and number is not None and len(stem.split()) >= 2:
                return stem, number
    return None


def parse_series_number(value: str) -> Optional[int]:
    if value.casefold() in SERIES_NUMBER_WORDS:
        return SERIES_NUMBER_WORDS[value.casefold()]
    if value.isdigit():
        return int(value)
    return parse_roman_number(value)


def parse_roman_number(value: str) -> Optional[int]:
    roman_values = {"i": 1, "v": 5, "x": 10, "l": 50, "c": 100, "d": 500, "m": 1000}
    total = 0
    previous = 0
    for character in reversed(value.casefold()):
        current = roman_values.get(character)
        if current is None:
            return None
        if current < previous:
            total -= current
        else:
            total += current
            previous = current
    return total if total > 0 else None
