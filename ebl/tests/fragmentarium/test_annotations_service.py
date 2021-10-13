from ebl.ebl_ai_client import EblAiClient
from ebl.fragmentarium.application.annotations_schema import AnnotationsSchema
from ebl.fragmentarium.application.annotations_service import AnnotationsService
from ebl.fragmentarium.domain.annotation import Annotations
from ebl.fragmentarium.domain.museum_number import MuseumNumber
from ebl.tests.factories.annotation import AnnotationsFactory

SCHEMA = AnnotationsSchema()


def test_generate_annotations(
    annotations_repository, photo_repository, changelog, when, photo_jpeg
):
    fragment_number = MuseumNumber.of("X.0")

    image_file = photo_jpeg

    when(photo_repository).query_by_file_name(f"{fragment_number}.jpg").thenReturn(
        image_file
    )
    ebl_ai_client = EblAiClient("mock-localhost:8001")
    service = AnnotationsService(
        ebl_ai_client, annotations_repository, photo_repository, changelog
    )

    expected = Annotations(fragment_number, tuple())
    when(ebl_ai_client).generate_annotations(fragment_number, image_file, 0).thenReturn(
        expected
    )

    annotations = service.generate_annotations(fragment_number, 0)
    assert isinstance(annotations, Annotations)
    assert annotations == expected


def test_find(annotations_repository, photo_repository, changelog, when):
    annotations = AnnotationsFactory.build()
    when(annotations_repository).query_by_museum_number(
        annotations.fragment_number
    ).thenReturn(annotations)
    service = AnnotationsService(
        EblAiClient(""), annotations_repository, photo_repository, changelog
    )

    assert service.find(annotations.fragment_number) == annotations


def test_update(annotations_repository, photo_repository, when, user, changelog):
    fragment_number = MuseumNumber("K", "1")
    annotations = AnnotationsFactory.build(fragment_number=fragment_number)
    updated_annotations = AnnotationsFactory.build(fragment_number=fragment_number)

    when(annotations_repository).query_by_museum_number(fragment_number).thenReturn(
        annotations
    )
    when(annotations_repository).create_or_update(updated_annotations).thenReturn()
    when(changelog).create(
        "annotations",
        user.profile,
        {"_id": str(fragment_number), **SCHEMA.dump(annotations)},
        {"_id": str(fragment_number), **SCHEMA.dump(updated_annotations)},
    ).thenReturn()

    service = AnnotationsService(
        EblAiClient(""), annotations_repository, photo_repository, changelog
    )

    assert service.update(updated_annotations, user) == updated_annotations
