from typing import Sequence, cast

import pytest

from ebl.media.application import (
    BackfillCategory,
    BackfillReport,
    BackfillRequest,
    ImportMode,
    ImportRequest,
)
from ebl.transliteration.domain.museum_number import MuseumNumber

FRAGMENT_ID = MuseumNumber.of("K.1")
OTHER_FRAGMENT_ID = MuseumNumber.of("K.2")


def import_request(
    fragment_ids: Sequence[MuseumNumber] = (), *, dry_run: bool = False
) -> ImportRequest:
    return ImportRequest(
        ImportMode.REPLACE, "photo-archive", fragment_ids, dry_run=dry_run
    )


def test_import_request_deduplicates_fragment_ids_in_first_seen_order() -> None:
    request = import_request((OTHER_FRAGMENT_ID, FRAGMENT_ID, OTHER_FRAGMENT_ID))

    assert request.fragment_ids == (OTHER_FRAGMENT_ID, FRAGMENT_ID)


def test_import_request_rejects_a_non_boolean_dry_run() -> None:
    with pytest.raises(ValueError, match="dry_run must be a boolean"):
        import_request(dry_run=cast(bool, "yes"))


def test_import_request_accepts_both_boolean_dry_run_values() -> None:
    assert import_request(dry_run=True).dry_run is True
    assert import_request().dry_run is False


def test_backfill_request_defaults_to_a_bounded_dry_run() -> None:
    request = BackfillRequest()

    assert request.dry_run is True
    assert request.batch_size == 100
    assert request.resume_after is None


def test_backfill_request_rejects_a_non_boolean_dry_run() -> None:
    with pytest.raises(ValueError, match="dry_run must be a boolean"):
        BackfillRequest(dry_run=cast(bool, "yes"))


@pytest.mark.parametrize("batch_size", [0, -5])
def test_backfill_request_rejects_a_non_positive_batch_size(batch_size: int) -> None:
    with pytest.raises(ValueError, match="batch_size must be positive"):
        BackfillRequest(batch_size=batch_size)


def test_backfill_request_rejects_a_non_integer_batch_size() -> None:
    with pytest.raises(ValueError, match="batch_size must be an integer"):
        BackfillRequest(batch_size=True)


def test_backfill_request_rejects_an_absent_batch_size() -> None:
    with pytest.raises(ValueError, match="batch_size must be an integer"):
        BackfillRequest(batch_size=cast(int, None))


def test_backfill_request_rejects_a_blank_resume_cursor() -> None:
    with pytest.raises(ValueError, match="resume_after cannot be blank"):
        BackfillRequest(resume_after=" ")


def test_backfill_request_accepts_a_bounded_resumed_run() -> None:
    request = BackfillRequest(dry_run=False, batch_size=100, resume_after="cursor-2")

    assert (request.dry_run, request.batch_size, request.resume_after) == (
        False,
        100,
        "cursor-2",
    )


def test_backfill_report_is_hashable() -> None:
    report = BackfillReport(
        report_entries=((BackfillCategory.UNKNOWN_FRAGMENT, ("K.999",)),)
    )

    assert hash(report) == hash(
        BackfillReport(
            report_entries=((BackfillCategory.UNKNOWN_FRAGMENT, ("K.999",)),)
        )
    )


def test_backfill_report_orders_entries_canonically() -> None:
    report = BackfillReport(
        report_entries=(
            (BackfillCategory.UNKNOWN_FRAGMENT, ["K.999"]),
            (BackfillCategory.AMBIGUOUS_FILENAME, ["a.jpg"]),
        )
    )

    assert report.report_entries == (
        (BackfillCategory.AMBIGUOUS_FILENAME, ("a.jpg",)),
        (BackfillCategory.UNKNOWN_FRAGMENT, ("K.999",)),
    )


def test_backfill_reports_with_the_same_findings_are_equal_and_hash_alike() -> None:
    findings: Sequence[tuple[BackfillCategory, Sequence[str]]] = (
        (BackfillCategory.UNKNOWN_FRAGMENT, ("K.999",)),
        (BackfillCategory.ORPHANED_ORIGINAL, ("original-1",)),
    )

    report = BackfillReport(report_entries=findings)
    same_report = BackfillReport(report_entries=tuple(reversed(findings)))

    assert report == same_report
    assert hash(report) == hash(same_report)
