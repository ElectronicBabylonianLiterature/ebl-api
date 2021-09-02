from PIL import Image
from mockito import mock, verify

import ebl.fragmentarium.retrieve_annotations as retrieve_annotations
from ebl.fragmentarium.domain.museum_number import MuseumNumber
from ebl.fragmentarium.retrieve_annotations import create_annotations, BoundingBox, Point
from ebl.tests.factories.annotation import AnnotationsFactory, GeometryFactory
from ebl.tests.factories.fragment import TransliteratedFragmentFactory


def test_create_annotations(context, when, photo):
    annotation_repository = context.annotations_repository
    fragment_repository = context.fragment_repository
    annotation = AnnotationsFactory.build(fragment_number=MuseumNumber.of("X.0"))
    fragment = TransliteratedFragmentFactory.build(number=MuseumNumber.of("X.0"))

    image = mock({"save": lambda _: None, "size": (640, 480, 3)})
    fragment_repository.create(fragment)
    annotation_repository.create_or_update(annotation)
    when(context.photo_repository).query_by_file_name(...).thenReturn(photo)
    when(Image).open(...).thenReturn(image)
    when(retrieve_annotations).write_annotations(...).thenReturn(None)

    create_annotations([annotation], "", "", context)
    verify(image).save(f"{fragment.number}.jpg")


def test_bbox_from_geometry():
    geometry = GeometryFactory.build(x=0, y=0, width=100, height=100)
    shape = (640, 480)
    assert BoundingBox.from_relative_to_absolute_coordinates(
        image_width=shape[0], image_height=shape[1], geometry=geometry
    ) == (BoundingBox(Point(0, 0), Point(640, 0), Point(640, 480), Point(0, 480)))
