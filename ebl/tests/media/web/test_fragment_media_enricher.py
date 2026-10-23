from typing import Sequence

from ebl.media.application.default_media_service import DefaultMediaService
from ebl.media.domain import Media
from ebl.media.web.fragment_media_enricher import FragmentMediaEnricher
from ebl.tests.media.factories import (
    association,
    copy_media,
    photo_media,
    stored_media_sequence,
)
from ebl.tests.media.in_memory_media import (
    InMemoryMediaRepository,
    InMemoryRepresentationStore,
)
from ebl.transliteration.domain.museum_number import MuseumNumber

NUMBER = MuseumNumber.of("K.1")
DOCUMENT = {"museumNumber": {"prefix": "K", "number": "1", "suffix": ""}}


def enricher(*items: Media) -> FragmentMediaEnricher:
    return FragmentMediaEnricher(
        DefaultMediaService(
            InMemoryMediaRepository(stored_media_sequence(*items)),
            InMemoryRepresentationStore(),
        )
    )


def test_disabled_enrichment_preserves_response_exactly() -> None:
    media = FragmentMediaEnricher()
    assert media.enrich(DOCUMENT, NUMBER) is DOCUMENT
    assert media.enrich_rows([DOCUMENT]) == [DOCUMENT]


def test_empty_page_needs_no_media_queries() -> None:
    assert enricher().enrich_rows([]) == []


def test_empty_new_media_preserves_existing_photo_and_thumbnail() -> None:
    document = {**DOCUMENT, "hasPhoto": True, "thumbnailPath": "/legacy/custom"}
    result = enricher().enrich(document, NUMBER)
    assert result["hasPhoto"] is True
    assert result["legacyHasPhoto"] is True
    assert result["thumbnailPath"] == "/legacy/custom"
    assert result["mediaSummary"] == {"count": 0, "types": []}
    assert "mediaSummary" not in document


def test_copy_only_fragment_has_a_summary_without_claiming_a_photo() -> None:
    result = enricher(copy_media()).enrich(DOCUMENT, NUMBER)
    assert result["hasPhoto"] is False
    assert result["legacyHasPhoto"] is False
    assert result["mediaSummary"]["types"] == ["COPY"]
    assert result["mediaSummary"]["primary"]["type"] == "COPY"


def test_new_photo_sets_flag_and_keeps_legacy_thumbnail_contract() -> None:
    result = enricher(photo_media()).enrich(DOCUMENT, NUMBER)
    assert result["hasPhoto"] is True
    assert result["legacyHasPhoto"] is False
    assert result["thumbnailPath"] == "/fragments/K.1/thumbnail/small"
    assert result["mediaSummary"]["primary"]["thumbnail"]["url"].startswith("/media/")


def test_original_only_nonprimary_media_remains_discoverable() -> None:
    media = photo_media(associations=(association(is_primary=False),))
    result = enricher(media).enrich(DOCUMENT, NUMBER)
    assert result["mediaSummary"] == {"count": 1, "types": ["PHOTO"]}
    assert result["hasPhoto"] is True


def test_page_reads_media_in_one_batch() -> None:
    class BatchRepository(InMemoryMediaRepository):
        def find_by_fragment(self, fragment_id: MuseumNumber) -> Sequence[Media]:
            raise AssertionError("Per-fragment read is not a batch.")

    media = photo_media()
    service = DefaultMediaService(
        BatchRepository(stored_media_sequence(media)), InMemoryRepresentationStore()
    )
    result = FragmentMediaEnricher(service).enrich_rows([DOCUMENT, DOCUMENT])
    assert len(result) == 2
    assert all(item["mediaSummary"]["count"] == 1 for item in result)
