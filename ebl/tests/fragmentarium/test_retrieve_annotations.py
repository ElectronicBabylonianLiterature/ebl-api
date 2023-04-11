from PIL import Image
from mockito import mock, verify

from ebl.fragmentarium.annotations_ import retrieve_annotations
from ebl.fragmentarium.domain.annotation import AnnotationValueType
from ebl.fragmentarium.annotations_.retrieve_annotations import create_annotations, BoundingBox
from ebl.tests.factories.annotation import (
    AnnotationsFactory,
    GeometryFactory,
    AnnotationDataFactory,
    AnnotationFactory,
)


def test_handle_blank_annotation_type():
    annotation_data = AnnotationDataFactory.build(type=AnnotationValueType.BLANK)
    assert retrieve_annotations.handle_blank_annotation_type(annotation_data) == "BLANK"
    annotation_data = AnnotationDataFactory.build()
    assert (
            retrieve_annotations.handle_blank_annotation_type(annotation_data)
            == annotation_data.sign_name
    )
    annotation_data = AnnotationDataFactory.build(sign_name="")
    assert (
            retrieve_annotations.handle_blank_annotation_type(annotation_data)
            == annotation_data.value
    )


def test_prepare_annotations():
    annotations_1 = AnnotationFactory.build()
    annotations_2 = AnnotationFactory.build(
        data=AnnotationDataFactory.build(type=AnnotationValueType.RULING_DOLLAR_LINE)
    )
    annotations_3 = AnnotationFactory.build(
        data=AnnotationDataFactory.build(sign_name="")
    )
    annotation = AnnotationsFactory.build(
        annotations=[annotations_1, annotations_2, annotations_3]
    )

    bounding_boxes, signs = retrieve_annotations.prepare_annotations(
        annotation, 100, 100
    )
    assert len(bounding_boxes) == 2
    assert len(signs) == 2
    assert signs[0] == annotations_1.data.sign_name
    assert signs[1] == annotations_3.data.value


def test_create_annotations(photo_repository, when, photo):
    annotation = AnnotationsFactory.build()

    image = mock({"save": lambda _: None, "size": (640, 480, 3)})
    when(photo_repository).query_by_file_name(
        f"{annotation.fragment_number}.jpg"
    ).thenReturn(photo)
    when(Image).open(...).thenReturn(image)
    when(retrieve_annotations).write_annotations(...).thenReturn(None)

    create_annotations([annotation], "", "", photo_repository)
    verify(image).save(f"{annotation.fragment_number}.jpg")


def test_from_relative_to_absolute_coordinates():
    geometry = GeometryFactory.build(x=0, y=0, width=100, height=100)
    shape = (640, 480)
    assert BoundingBox.from_relative_coordinates(
        geometry.x,
        geometry.y,
        geometry.width,
        geometry.height,
        image_width=shape[0],
        image_height=shape[1],
    ) == (BoundingBox(0, 0, 640, 480))


def test_write_annotations(tmp_path):
    dir = tmp_path / "annotations"
    dir.mkdir()
    file_name = dir / "annotation_1.txt"
    bounding_boxes = [BoundingBox(0.1, 1, 2, 100.543), BoundingBox(10, 11, 12, 13)]
    retrieve_annotations.write_annotations(
        file_name, bounding_boxes, ["KUR", "A.GUD×KUR"]
    )
    assert file_name.read_text() == "0,1,2,100,KUR\n10,11,12,13,A.GUD×KUR\n"


def test_write_fragment_numbers(tmp_path):
    annotations = AnnotationsFactory.build_batch(5)
    dir = tmp_path / "annotations"
    dir.mkdir()
    file_name = dir / "Annotation_numbers.txt"
    retrieve_annotations.write_fragment_numbers(annotations, file_name)
    result = "\n".join([str(annotation.fragment_number) for annotation in annotations])
    assert file_name.read_text() == f"Total of 5 Annotations\n{result}\n"
