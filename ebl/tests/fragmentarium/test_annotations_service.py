import io

import requests
from PIL import Image
from mockito import mock

from ebl.fragmentarium.application.annotations_schema import AnnotationsSchema
from ebl.fragmentarium.application.annotations_service import AnnotationsService
from ebl.fragmentarium.domain.annotation import Annotations
from ebl.fragmentarium.domain.museum_number import MuseumNumber
from ebl.tests.conftest import FakeFile
from ebl.tests.factories.annotation import AnnotationsFactory

SCHEMA = AnnotationsSchema()


def test_generate_annotations(
    annotations_repository, photo_repository, changelog, when
):
    fragment_number = MuseumNumber.of("X.0")
    image = Image.open("./test_image.jpeg")
    buf = io.BytesIO()
    image.save(buf, format="JPEG")
    image_file = FakeFile(str(fragment_number), buf.getvalue(), {})

    when(photo_repository).query_by_file_name(f"{fragment_number}.jpg").thenReturn(
        image_file
    )
    service = AnnotationsService(annotations_repository, photo_repository, changelog)
    boundary_results = {
        "boundaryResults": [
            {
                "top_left_x": 0.0,
                "top_left_y": 0.0,
                "width": 10.0,
                "height": 10.0,
                "probability": 0.99,
            }
        ]
    }

    when(requests).post(...).thenReturn(
        mock({"json": lambda: boundary_results, "status_code": 200})
    )
    annotations = service.generate_annotations(fragment_number, 0)
    assert isinstance(annotations, Annotations)
    assert len(annotations.annotations) > 0


def test_find(annotations_repository, changelog, when):
    annotations = AnnotationsFactory.build()
    when(annotations_repository).query_by_museum_number(
        annotations.fragment_number
    ).thenReturn(annotations)
    service = AnnotationsService(annotations_repository, changelog)

    assert service.find(annotations.fragment_number) == annotations


def test_update(annotations_repository, when, user, changelog):
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

    service = AnnotationsService(annotations_repository, changelog)

    assert service.update(updated_annotations, user) == updated_annotations
