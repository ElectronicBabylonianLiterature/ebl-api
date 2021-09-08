from PIL import Image
from mockito import mock, verify

import ebl.fragmentarium.retrieve_annotations as retrieve_annotations
from ebl.fragmentarium.retrieve_annotations import (
    create_annotations,
    BoundingBox,
    Point,
)
from ebl.tests.factories.annotation import AnnotationsFactory, GeometryFactory


def test_create_annotations(photo_repository, when, photo):
    annotation = AnnotationsFactory.build()
    image = mock({"save": lambda _: None, "size": (640, 480, 3)})
    when(photo_repository).query_by_file_name(
        f"{annotation.fragment_number}.jpg"
    ).thenReturn(photo)
    when(Image).open(...).thenReturn(image)

    create_annotations([annotation], "", "", photo_repository)
    verify(image).save(f"{annotation.fragment_number}.jpg")


def test_from_relative_to_absolute_coordinates():
    geometry = GeometryFactory.build(x=0, y=0, width=100, height=100)
    shape = (640, 480)
    assert BoundingBox.from_relative_to_absolute_coordinates(
        geometry.x,
        geometry.y,
        geometry.width,
        geometry.height,
        image_width=shape[0],
        image_height=shape[1],
    ) == (BoundingBox(Point(0, 0), Point(640, 0), Point(640, 480), Point(0, 480)))
