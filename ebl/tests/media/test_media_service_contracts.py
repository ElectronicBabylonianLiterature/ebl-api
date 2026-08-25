from types import MappingProxyType

from ebl.media.application import BackfillCategory, BackfillReport, ImportReport
from ebl.media.domain import Media, MediaAssociation, MediaId, MediaType
from ebl.tests.media.factories import (
    contract_media,
    stored_media,
    stored_media_sequence,
)
from ebl.tests.media.in_memory_media import (
    InMemoryMediaRepository,
)
from ebl.tests.media.in_memory_media_service import InMemoryMediaService
from ebl.transliteration.domain.museum_number import MuseumNumber

PHOTO_ID = MediaId("550e8400-e29b-41d4-a716-446655440000")
COPY_ID = MediaId("550e8400-e29b-41d4-a716-446655440001")
K1 = MuseumNumber.of("K.1")
SM2 = MuseumNumber.of("Sm.2")


def shared_photo() -> Media:
    return contract_media(
        PHOTO_ID,
        MediaType.PHOTO,
        (MediaAssociation(K1, 0, True), MediaAssociation(SM2, 0, True)),
    )


def test_service_lists_fragment_media_in_canonical_order() -> None:
    photo = contract_media(PHOTO_ID, MediaType.PHOTO, (MediaAssociation(K1, 1, False),))
    copy = contract_media(COPY_ID, MediaType.COPY, (MediaAssociation(K1, 0, True),))
    service = InMemoryMediaService(
        InMemoryMediaRepository(stored_media_sequence(photo, copy))
    )

    assert service.list_fragment_media(K1) == (copy, photo)


def test_service_batch_reads_return_raw_domain_media_for_every_fragment() -> None:
    photo = shared_photo()
    missing = MuseumNumber.of("BM.99")
    service = InMemoryMediaService(
        InMemoryMediaRepository(stored_media_sequence(photo))
    )

    assert service.find_media_by_fragments((K1, SM2, missing)) == {
        K1: (photo,),
        SM2: (photo,),
        missing: (),
    }


def test_service_reads_one_media_item_only_within_its_fragment() -> None:
    service = InMemoryMediaService(
        InMemoryMediaRepository(
            stored_media_sequence(
                contract_media(
                    PHOTO_ID, MediaType.PHOTO, (MediaAssociation(K1, 0, True),)
                ),
            )
        )
    )

    assert service.get_fragment_media(K1, PHOTO_ID) is not None
    assert service.get_fragment_media(SM2, PHOTO_ID) is None


def test_service_reads_stored_media_item_in_fragment_context() -> None:
    stored = stored_media(shared_photo(), "current")
    service = InMemoryMediaService(InMemoryMediaRepository((stored,)))

    result = service.get_stored_fragment_media(K1, PHOTO_ID)

    assert result == stored
    assert service.get_stored_fragment_media(MuseumNumber.of("BM.99"), PHOTO_ID) is None


def test_shared_media_appears_under_every_requested_fragment() -> None:
    photo = shared_photo()
    service = InMemoryMediaService(
        InMemoryMediaRepository(stored_media_sequence(photo))
    )

    result = service.find_media_by_fragments((K1, SM2))

    assert result[K1] == result[SM2] == (photo,)


def test_import_report_distinguishes_every_outcome() -> None:
    report = ImportReport()

    assert (report.created, report.skipped, report.replaced, report.failed) == (
        0,
        0,
        0,
        0,
    )
    assert report.errors == ()
    assert report.warnings == ()


def test_backfill_report_defaults_to_an_empty_completed_summary() -> None:
    report = BackfillReport()

    counts = (
        report.scanned,
        report.candidates,
        report.created,
        report.replaced,
        report.skipped,
        report.failed,
    )

    assert counts == (0, 0, 0, 0, 0, 0)
    assert report.next_resume_token is None
    assert report.reports == {}


def test_backfill_report_carries_a_resume_token_and_typed_categories() -> None:
    report = BackfillReport(
        scanned=100,
        candidates=40,
        created=38,
        failed=2,
        next_resume_token="cursor-2",
        reports={BackfillCategory.UNKNOWN_FRAGMENT: ["K.999"]},
    )

    assert report.next_resume_token == "cursor-2"
    assert report.reports[BackfillCategory.UNKNOWN_FRAGMENT] == ("K.999",)


def test_backfill_report_collections_cannot_be_mutated_by_the_caller() -> None:
    entries = ["K.999"]
    report = BackfillReport(reports={BackfillCategory.UNKNOWN_FRAGMENT: entries})

    entries.append("K.1000")

    assert report.reports[BackfillCategory.UNKNOWN_FRAGMENT] == ("K.999",)
    assert isinstance(report.reports, MappingProxyType)
