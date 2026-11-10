from typing import Sequence

import pytest
from pymongo.database import Database

from ebl.context import Context
from ebl.fragmentarium.application.cropped_annotations_service import (
    CroppedAnnotationService,
)
from ebl.fragmentarium.domain.date import DateSchema
from ebl.media.application.default_media_service import DefaultMediaService
from ebl.media.infrastructure.mongo_media_reader import MongoMediaReader
from ebl.media.web.fragment_media_enricher import FragmentMediaEnricher
from ebl.tests.media.in_memory_media import (
    InMemoryMediaRepository,
    InMemoryRepresentationStore,
)
from ebl.tests.factories.annotation import AnnotationsWithScriptFactory
from ebl.tests.factories.fragment import FragmentFactory
from ebl.transliteration.domain.museum_number import MuseumNumber


class Visibility:
    def __init__(self, suppressed: frozenset[MuseumNumber]) -> None:
        self.suppressed = suppressed
        self.calls: list[tuple[MuseumNumber, ...]] = []

    def suppressed_legacy_fragments(
        self, fragment_ids: Sequence[MuseumNumber]
    ) -> frozenset[MuseumNumber]:
        self.calls.append(tuple(fragment_ids))
        return self.suppressed.intersection(fragment_ids)

    def legacy_fallback_allowed(self, fragment_id: MuseumNumber) -> bool:
        return fragment_id not in self.suppressed_legacy_fragments((fragment_id,))


def test_disabled_media_enrichment_honors_takedown_without_adding_fields() -> None:
    number = MuseumNumber.of("K.1")
    visibility = Visibility(frozenset((number,)))
    document = {"hasPhoto": True, "thumbnailPath": "/legacy/thumbnail"}

    result = FragmentMediaEnricher(legacy_visibility=visibility).enrich(
        document, number
    )

    assert result == {"hasPhoto": False, "thumbnailPath": "/legacy/thumbnail"}
    assert document == {"hasPhoto": True, "thumbnailPath": "/legacy/thumbnail"}
    assert visibility.calls == [(number,)]


def test_disabled_media_page_visibility_is_batched_and_keeps_unsuppressed_rows() -> (
    None
):
    hidden, visible = MuseumNumber.of("K.1"), MuseumNumber.of("K.2")
    visibility = Visibility(frozenset((hidden,)))
    documents = [
        {
            "museumNumber": {"prefix": "K", "number": number, "suffix": ""},
            "hasPhoto": True,
        }
        for number in ("1", "2")
    ]

    result = FragmentMediaEnricher(legacy_visibility=visibility).enrich_rows(documents)

    assert result == [{**documents[0], "hasPhoto": False}, documents[1]]
    assert result[1] is documents[1]
    assert visibility.calls == [(hidden, visible)]
    assert all("mediaSummary" not in document for document in result)


def test_explicit_visibility_takes_precedence_over_the_optional_media_service() -> None:
    number = MuseumNumber.of("K.1")
    service = DefaultMediaService(
        InMemoryMediaRepository(), InMemoryRepresentationStore()
    )
    visibility = Visibility(frozenset((number,)))

    result = FragmentMediaEnricher(service, visibility).enrich(
        {"hasPhoto": True}, number
    )

    assert result == {"hasPhoto": False, "mediaSummary": {"count": 0, "types": []}}
    assert visibility.calls == [(number,)]


def test_read_only_visibility_does_not_create_collections(database: Database) -> None:
    before = set(database.list_collection_names())
    visibility = MongoMediaReader(database)
    number = MuseumNumber.of("K.100")

    assert visibility.legacy_fallback_allowed(number)
    assert set(database.list_collection_names()) == before
    database["mediaLegacyVisibility"].insert_one(
        {"_id": str(number), "suppressed": True}
    )
    assert not visibility.legacy_fallback_allowed(number)


def test_cropped_dates_reject_non_object_schema_output(
    context: Context, monkeypatch: pytest.MonkeyPatch
) -> None:
    annotations = AnnotationsWithScriptFactory.build()
    context.fragment_repository.create(
        FragmentFactory.build(number=annotations.fragment_number)
    )
    service = CroppedAnnotationService(
        context.annotations_repository,
        context.cropped_sign_images_repository,
        context.fragment_repository,
    )
    monkeypatch.setattr(DateSchema, "dump", lambda *_args, **_kwargs: [])
    date_cache: dict[str, dict] = {}

    with pytest.raises(TypeError, match="A fragment date must serialize to an object"):
        service._find_fragment_date(annotations, date_cache)

    assert date_cache == {}
