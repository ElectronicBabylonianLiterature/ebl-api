import attr

from ebl.fragmentarium.domain.annotation import AnnotationValueType
from ebl.fragmentarium.update_annotations import parse_value, update_annotations
from ebl.tests.factories.annotation import (
    AnnotationsFactory,
    AnnotationDataFactory,
    AnnotationFactory,
)


def test_parse_value_1():
    reading = "kib₂"
    result = parse_value(reading)
    assert result[0] == "kib"
    assert result[1] == 2


def test_parse_value_2():
    reading = "kibₓ"
    result = parse_value(reading)
    assert result[0] == "kib"
    assert result[1] is None


def test_update_annotations(context, signs, when):
    sign = signs[0]

    annotations_repository = context.annotations_repository
    sign_repository = context.sign_repository

    annotation_data = AnnotationDataFactory.build_batch(2, sign_name="", value="kib₂")
    annotation_1 = AnnotationFactory.build(data=annotation_data[0])
    annotation_2 = AnnotationFactory.build(data=annotation_data[1])
    annotation = AnnotationsFactory.build(annotations=[annotation_1, annotation_2])

    when(annotations_repository).retrieve_all().thenReturn([annotation])
    when(sign_repository).search(...).thenReturn(sign)

    expected_annotation_data_1 = attr.evolve(
        annotation_data[0], sign_name=sign.name, type=AnnotationValueType.READING
    )
    expected_annotation_data_2 = attr.evolve(
        annotation_data[1], sign_name=sign.name, type=AnnotationValueType.READING
    )
    expected_annotation_1 = attr.evolve(annotation_1, data=expected_annotation_data_1)
    expected_annotation_2 = attr.evolve(annotation_2, data=expected_annotation_data_2)
    expected = attr.evolve(
        annotation, annotations=[expected_annotation_1, expected_annotation_2]
    )

    update_annotations(annotations_repository, sign_repository)

    annotation_with_sign = annotations_repository.query_by_museum_number(
        annotation.fragment_number
    )

    assert annotation_with_sign == expected
