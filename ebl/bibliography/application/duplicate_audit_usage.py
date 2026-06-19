from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Optional


@dataclass
class UsageCounts:
    fragments: int = 0
    corpus_texts: int = 0
    corpus_manuscripts: int = 0
    dossiers: int = 0
    note_markup: int = 0
    fully_checked: bool = True

    @property
    def total(self) -> int:
        return (
            self.fragments
            + self.corpus_texts
            + self.corpus_manuscripts
            + self.dossiers
            + self.note_markup
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "total": self.total,
            "fragments": self.fragments,
            "corpusTexts": self.corpus_texts,
            "corpusManuscripts": self.corpus_manuscripts,
            "dossiers": self.dossiers,
            "noteMarkup": self.note_markup,
            "fullyChecked": self.fully_checked,
        }


def collect_usage_counts(database: Any, ids: Iterable[str]) -> dict[str, UsageCounts]:
    counts = {id_: UsageCounts() for id_ in ids}
    for id_ in counts:
        assign_count(
            counts[id_],
            "fragments",
            count_documents(database, "fragments", {"references.id": id_}),
        )
        assign_count(
            counts[id_],
            "corpus_texts",
            count_documents(database, "texts", {"references.id": id_}),
        )
        assign_count(
            counts[id_],
            "corpus_manuscripts",
            count_documents(
                database,
                "chapters",
                {
                    "$or": [
                        {"manuscripts.references.id": id_},
                        {"manuscripts.oldSigla.reference.id": id_},
                    ]
                },
            ),
        )
        assign_count(
            counts[id_],
            "dossiers",
            count_documents(database, "dossiers", {"references.id": id_}),
        )
    add_note_markup_counts(database, counts)
    return counts


def count_documents(
    database: Any, collection: str, query: Mapping[str, Any]
) -> Optional[int]:
    try:
        return database[collection].count_documents(query)
    except Exception:
        return None


def assign_count(usage: UsageCounts, field_name: str, count: Optional[int]) -> None:
    if count is None:
        usage.fully_checked = False
        setattr(usage, field_name, 0)
    else:
        setattr(usage, field_name, count)


def add_note_markup_counts(database: Any, counts: dict[str, UsageCounts]) -> None:
    if not counts:
        return
    pattern = re.compile(r"@bib\{([^@{}]+)")
    for collection, fields in note_markup_collections().items():
        add_collection_note_markup_counts(database, counts, collection, fields, pattern)


def note_markup_collections() -> dict[str, tuple[str, ...]]:
    return {
        "fragments": (
            "notes.text",
            "introduction.text",
            "text.lines.content.value",
        ),
        "chapters": (
            "lines.variants.note.parts.value",
            "manuscripts.notes",
        ),
        "texts": ("intro",),
    }


def add_collection_note_markup_counts(
    database: Any,
    counts: dict[str, UsageCounts],
    collection: str,
    fields: tuple[str, ...],
    pattern: re.Pattern[str],
) -> None:
    try:
        cursor = database[collection].find({}, dict.fromkeys(fields, 1))
    except Exception:
        mark_usage_counts_incomplete(counts)
        return
    for document in cursor:
        for id_ in note_markup_ids(document, pattern):
            if id_ in counts:
                counts[id_].note_markup += 1


def mark_usage_counts_incomplete(counts: Mapping[str, UsageCounts]) -> None:
    for usage in counts.values():
        usage.fully_checked = False


def note_markup_ids(document: Any, pattern: re.Pattern[str]) -> list[str]:
    return [
        match.group(1) for match in pattern.finditer(json.dumps(document, default=str))
    ]
