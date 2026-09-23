from typing import Sequence, cast

import pytest

from ebl.media.application import (
    BackfillCategory,
    BackfillReport,
    BackfillRequest,
    ImportMode,
    ImportReport,
    ImportRequest,
    MAX_BACKFILL_BATCH_SIZE,
)
from ebl.transliteration.domain.museum_number import MuseumNumber

FRAGMENT_ID = MuseumNumber.of("K.1")
OTHER_FRAGMENT_ID = MuseumNumber.of("K.2")
ReportEntries = Sequence[tuple[BackfillCategory, Sequence[str]]]


def import_request(
    fragment_ids: Sequence[MuseumNumber] = (), *, dry_run: bool = False
) -> ImportRequest:
    return ImportRequest(
        ImportMode.REPLACE, "photo-archive", fragment_ids, dry_run=dry_run
    )


def test_import_request_deduplicates_fragment_ids_in_first_seen_order() -> None:
    request = import_request((OTHER_FRAGMENT_ID, FRAGMENT_ID, OTHER_FRAGMENT_ID))

    assert request.fragment_ids == (OTHER_FRAGMENT_ID, FRAGMENT_ID)


def test_import_request_rejects_a_bare_string_fragment_collection() -> None:
    with pytest.raises(ValueError, match="fragment_ids must be a sequence"):
        import_request(cast(Sequence[MuseumNumber], "K.1"))


def test_import_request_rejects_non_museum_number_members() -> None:
    with pytest.raises(ValueError, match="contain only museum numbers"):
        import_request((cast(MuseumNumber, "K.1"), FRAGMENT_ID))


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


def test_backfill_request_rejects_a_batch_above_the_maximum() -> None:
    with pytest.raises(ValueError, match="batch_size must be at most 1000"):
        BackfillRequest(batch_size=MAX_BACKFILL_BATCH_SIZE + 1)


def test_backfill_request_rejects_a_blank_resume_cursor() -> None:
    with pytest.raises(ValueError, match="resume_after cannot be blank"):
        BackfillRequest(resume_after=" ")


def test_backfill_request_accepts_a_bounded_resumed_run() -> None:
    request = BackfillRequest(
        dry_run=False,
        batch_size=MAX_BACKFILL_BATCH_SIZE,
        resume_after="cursor-2",
    )

    assert (request.dry_run, request.batch_size, request.resume_after) == (
        False,
        MAX_BACKFILL_BATCH_SIZE,
        "cursor-2",
    )

    assert BackfillRequest(batch_size=1).batch_size == 1


def test_backfill_report_merges_repeated_categories_without_losing_findings() -> None:
    report = BackfillReport(
        report_entries=(
            (BackfillCategory.UNKNOWN_FRAGMENT, ["K.2", "K.1"]),
            (BackfillCategory.AMBIGUOUS_FILENAME, ["a.jpg"]),
            (BackfillCategory.UNKNOWN_FRAGMENT, ["K.3"]),
        )
    )

    assert report.report_entries == (
        (BackfillCategory.AMBIGUOUS_FILENAME, ("a.jpg",)),
        (BackfillCategory.UNKNOWN_FRAGMENT, ("K.1", "K.2", "K.3")),
    )
    assert report.reports[BackfillCategory.UNKNOWN_FRAGMENT] == ("K.1", "K.2", "K.3")


def test_backfill_reports_with_the_same_findings_are_equal_and_hash_alike() -> None:
    findings: Sequence[tuple[BackfillCategory, Sequence[str]]] = (
        (BackfillCategory.UNKNOWN_FRAGMENT, ("K.2", "K.1")),
        (BackfillCategory.UNKNOWN_FRAGMENT, ("K.3",)),
        (BackfillCategory.ORPHANED_ORIGINAL, ("original-1",)),
    )
    reordered_findings: Sequence[tuple[BackfillCategory, Sequence[str]]] = (
        (BackfillCategory.ORPHANED_ORIGINAL, ("original-1",)),
        (BackfillCategory.UNKNOWN_FRAGMENT, ("K.3",)),
        (BackfillCategory.UNKNOWN_FRAGMENT, ("K.1", "K.2")),
    )

    report = BackfillReport(report_entries=findings)
    same_report = BackfillReport(report_entries=reordered_findings)

    assert report == same_report
    assert hash(report) == hash(same_report)
    assert report.report_entries == same_report.report_entries


def test_backfill_report_rejects_non_category_keys() -> None:
    entries = cast(
        Sequence[tuple[BackfillCategory, Sequence[str]]],
        (("unknown-fragment", ("K.1",)),),
    )

    with pytest.raises(ValueError, match="BackfillCategory members"):
        BackfillReport(report_entries=entries)


def test_backfill_report_rejects_malformed_pairs() -> None:
    entries = cast(
        Sequence[tuple[BackfillCategory, Sequence[str]]],
        ((BackfillCategory.UNKNOWN_FRAGMENT,),),
    )

    with pytest.raises(ValueError, match="must be a .* pair"):
        BackfillReport(report_entries=entries)


def test_string_collections_reject_bare_strings_and_non_string_members() -> None:
    with pytest.raises(ValueError, match="sequences of strings"):
        ImportReport(errors=cast(Sequence[str], "oops"))
    with pytest.raises(ValueError, match="contain only strings"):
        ImportReport(warnings=(cast(str, 1),))
    with pytest.raises(ValueError, match="sequences of strings"):
        BackfillReport(
            report_entries=(
                (
                    BackfillCategory.UNKNOWN_FRAGMENT,
                    cast(Sequence[str], "K.1"),
                ),
            )
        )


def test_sequence_fields_reject_non_sequence_inputs() -> None:
    with pytest.raises(ValueError):
        import_request(cast(Sequence[MuseumNumber], 1))
    with pytest.raises(ValueError):
        import_request(cast(Sequence[MuseumNumber], 0))
    with pytest.raises(ValueError):
        ImportReport(errors=cast(Sequence[str], 1))
    with pytest.raises(ValueError):
        BackfillReport(report_entries=cast(ReportEntries, "entries"))
    with pytest.raises(ValueError):
        BackfillReport(report_entries=cast(ReportEntries, 1))


def test_valid_import_report_string_collections_are_frozen() -> None:
    report = ImportReport(errors=["first", "second"], warnings=["warning"])

    assert report.errors == ("first", "second")
    assert report.warnings == ("warning",)
    assert ImportReport(errors=cast(Sequence[str], None)).errors == ()


@pytest.mark.parametrize(
    "counters",
    [(-1, 0, 0, 0), (0, -1, 0, 0), (0, 0, -1, 0), (0, 0, 0, -1)],
)
def test_import_report_rejects_negative_counters(
    counters: tuple[int, int, int, int],
) -> None:
    with pytest.raises(ValueError, match="cannot be negative"):
        ImportReport(*counters)


@pytest.mark.parametrize(
    "counters",
    [
        (-1, 0, 0, 0, 0, 0),
        (0, -1, 0, 0, 0, 0),
        (0, 0, -1, 0, 0, 0),
        (0, 0, 0, -1, 0, 0),
        (0, 0, 0, 0, -1, 0),
        (0, 0, 0, 0, 0, -1),
    ],
)
def test_backfill_report_rejects_negative_counters(
    counters: tuple[int, int, int, int, int, int],
) -> None:
    with pytest.raises(ValueError, match="cannot be negative"):
        BackfillReport(*counters)


def test_report_counters_reject_booleans() -> None:
    with pytest.raises(ValueError, match="created must be an integer"):
        ImportReport(created=cast(int, True))
    with pytest.raises(ValueError, match="scanned must be an integer"):
        BackfillReport(scanned=cast(int, False))


def test_backfill_report_rejects_a_blank_resume_token() -> None:
    with pytest.raises(ValueError, match="next_resume_token cannot be blank"):
        BackfillReport(next_resume_token=" ")


def test_backfill_resume_token_round_trips_into_the_next_request() -> None:
    report = BackfillReport(next_resume_token="cursor-3")
    request = BackfillRequest(resume_after=report.next_resume_token)

    assert request.resume_after == "cursor-3"
