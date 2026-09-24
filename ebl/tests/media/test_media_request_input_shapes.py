from typing import Sequence, cast

import pytest

from ebl.media.application import (
    BackfillCategory,
    BackfillReport,
    ImportMode,
    ImportReport,
    ImportRequest,
    MAX_IMPORT_FRAGMENT_IDS,
)
from ebl.transliteration.domain.museum_number import MuseumNumber

FRAGMENT_ID = MuseumNumber.of("K.1")
OTHER_FRAGMENT_ID = MuseumNumber.of("K.2")
ReportEntries = Sequence[tuple[BackfillCategory, Sequence[str]]]


def test_import_request_rejects_unordered_or_one_shot_iterables() -> None:
    with pytest.raises(ValueError, match="fragment_ids must be a sequence"):
        ImportRequest(
            ImportMode.REPLACE,
            "photo-archive",
            cast(Sequence[MuseumNumber], {FRAGMENT_ID, OTHER_FRAGMENT_ID}),
        )
    with pytest.raises(ValueError, match="fragment_ids must be a sequence"):
        ImportRequest(
            ImportMode.REPLACE,
            "photo-archive",
            cast(Sequence[MuseumNumber], (item for item in (FRAGMENT_ID,))),
        )


def test_import_request_rejects_an_invalid_mode_with_value_error() -> None:
    with pytest.raises(ValueError, match="mode must be a ImportMode"):
        ImportRequest(cast(ImportMode, "replace"), "photo-archive")


def test_import_request_rejects_too_many_fragments() -> None:
    fragment_ids = tuple(
        MuseumNumber("K", str(index)) for index in range(MAX_IMPORT_FRAGMENT_IDS + 1)
    )

    with pytest.raises(ValueError, match="at most 1000 museum numbers"):
        ImportRequest(ImportMode.REPLACE, "photo-archive", fragment_ids)


def test_string_collections_reject_unordered_or_one_shot_iterables() -> None:
    with pytest.raises(ValueError, match="sequences of strings"):
        ImportReport(errors=cast(Sequence[str], {"first", "second"}))
    with pytest.raises(ValueError, match="sequences of strings"):
        ImportReport(warnings=cast(Sequence[str], (item for item in ("warning",))))


def test_report_entries_reject_unordered_or_one_shot_iterables() -> None:
    entry = (BackfillCategory.UNKNOWN_FRAGMENT, ("K.1",))
    with pytest.raises(ValueError, match="sequence of pairs"):
        BackfillReport(report_entries=cast(ReportEntries, {entry}))
    with pytest.raises(ValueError, match="sequence of pairs"):
        BackfillReport(report_entries=cast(ReportEntries, (item for item in (entry,))))
