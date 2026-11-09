"""Annotation tooling must not read or expose removed legacy originals."""

from typing import cast

import pytest
from mockito import mock, verify, verifyZeroInteractions, when as mockito_when

from ebl.ebl_ai_client import EblAiClient
from ebl.errors import NotFoundError
from ebl.fragmentarium.application.annotations_repository import AnnotationsRepository
from ebl.fragmentarium.application.annotations_service import AnnotationsService
from ebl.fragmentarium.application.cropped_annotations_service import (
    CroppedAnnotationService,
)
from ebl.fragmentarium.application.cropped_sign_image import Base64, CroppedSignImage
from ebl.fragmentarium.application.cropped_sign_images_repository import (
    CroppedSignImagesRepository,
)
from ebl.tests.factories.annotation import (
    AnnotationFactory,
    AnnotationsFactory,
    AnnotationsWithScriptFactory,
)
from ebl.transliteration.domain.museum_number import MuseumNumber


class FakeMedia:
    def __init__(self, suppressed=()):
        self._suppressed = frozenset(suppressed)

    def suppressed_legacy_fragments(self, numbers):
        return self._suppressed & frozenset(numbers)

    def legacy_fallback_allowed(self, number):
        return number not in self._suppressed


NUMBER = MuseumNumber.of("K.1")


def _service(media):
    return AnnotationsService(
        cast(EblAiClient, mock()),
        cast(AnnotationsRepository, mock()),
        mock(),
        mock(),
        mock(),
        mock(),
        cast(CroppedSignImagesRepository, mock()),
        media,
    )


def test_generate_refuses_suppressed_original_before_reading_it():
    service = _service(FakeMedia({NUMBER}))
    with pytest.raises(NotFoundError):
        service.generate_annotations(NUMBER)
    verifyZeroInteractions(service._photo_repository)
    verifyZeroInteractions(service._ebl_ai_client)


def test_update_refuses_suppressed_original_without_side_effects():
    service = _service(FakeMedia({NUMBER}))
    annotations = AnnotationsFactory.build(fragment_number=NUMBER)
    with pytest.raises(NotFoundError):
        service.update(annotations, mock())
    verifyZeroInteractions(service._cropped_sign_images_repository)
    verifyZeroInteractions(service._annotations_repository)
    verifyZeroInteractions(service._changelog)
    verifyZeroInteractions(service._photos_repository)


def test_other_fragments_and_disabled_media_are_unchanged():
    photo = mock()
    expected = AnnotationsFactory.build(fragment_number=NUMBER)
    for media in (None, FakeMedia({MuseumNumber.of("K.2")})):
        service = _service(media)
        mockito_when(service._photo_repository).query_by_file_name(
            "K.1.jpg"
        ).thenReturn(photo)
        mockito_when(service._ebl_ai_client).generate_annotations(
            NUMBER, photo, 0.3
        ).thenReturn(expected)
        assert service.generate_annotations(NUMBER) == expected


def test_persisted_cropped_signs_of_suppressed_fragments_are_not_served(
    fragment_repository,
):
    hidden = AnnotationsWithScriptFactory.build(
        fragment_number=MuseumNumber.of("K.1"),
        annotations=[AnnotationFactory.build(cropped_sign__image_id="hidden")],
    )
    visible = AnnotationsWithScriptFactory.build(
        fragment_number=MuseumNumber.of("K.2"),
        annotations=[AnnotationFactory.build(cropped_sign__image_id="visible")],
    )
    annotations_repository = cast(AnnotationsRepository, mock())
    images = cast(CroppedSignImagesRepository, mock())
    mockito_when(annotations_repository).find_by_sign(
        "sign", False, False, None, None
    ).thenReturn([hidden, visible])
    mockito_when(images).query_by_id("visible").thenReturn(
        CroppedSignImage("visible", Base64("v"), visible.fragment_number)
    )
    mockito_when(fragment_repository).fetch_date(visible.fragment_number).thenReturn(
        None
    )
    service = CroppedAnnotationService(
        annotations_repository,
        images,
        fragment_repository,
        FakeMedia({hidden.fragment_number}),
    )

    result = service.find_annotations_by_sign("sign")

    assert [item["fragmentNumber"] for item in result] == ["K.2"]
    verify(images, times=0).query_by_id("hidden")
