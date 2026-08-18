import pytest

from ebl.fragmentarium.domain.annotation import AnnotationValueType
from ebl.fragmentarium.retrieve_annotations_helpers import (
    MINIMUM_BOUNDING_BOX_SIZE,
    create_directory,
    filter_empty_annotation,
    match,
    parse_annotations,
    prepare_annotations,
    sign_to_sign_ground_truth,
    write_annotations,
)
from ebl.tests.factories.annotation import (
    AnnotationDataFactory,
    AnnotationFactory,
    AnnotationsFactory,
    GeometryFactory,
)


def test_filter_empty_annotation_rejects_a_box_below_the_minimum() -> None:
    annotation = AnnotationFactory.build(
        geometry=GeometryFactory.build(width=MINIMUM_BOUNDING_BOX_SIZE / 2, height=10.0)
    )

    assert filter_empty_annotation(annotation) is False


def test_filter_empty_annotation_keeps_a_box_at_or_above_the_minimum() -> None:
    annotation = AnnotationFactory.build(
        geometry=GeometryFactory.build(width=10.0, height=10.0)
    )

    assert filter_empty_annotation(annotation) is True


@pytest.mark.parametrize(
    "annotation_type",
    [
        AnnotationValueType.SURFACE_AT_LINE,
        AnnotationValueType.BLANK,
        AnnotationValueType.ColumnAtLine,
        AnnotationValueType.STRUCT,
        AnnotationValueType.UnclearSign,
    ],
)
def test_match_returns_the_type_name(annotation_type) -> None:
    data = AnnotationDataFactory.build(type=annotation_type)

    assert match(data) == annotation_type.name


def test_match_marks_a_partially_broken_sign() -> None:
    data = AnnotationDataFactory.build(
        type=AnnotationValueType.PARTIALLY_BROKEN, sign_name="NUN", value="nun"
    )

    assert match(data) == "NUN?"


def test_match_falls_through_to_the_parsed_sign() -> None:
    data = AnnotationDataFactory.build(
        type=AnnotationValueType.HAS_SIGN, sign_name="NUN", value="nun"
    )

    assert match(data) == "NUN"


def test_parse_annotations_maps_a_lowercase_sign_name() -> None:
    data = AnnotationDataFactory.build(sign_name="ni", value="ni")

    assert parse_annotations(data) == "NI"


def test_parse_annotations_returns_a_digit_value_when_there_is_no_sign_name() -> None:
    data = AnnotationDataFactory.build(sign_name="", value="12")

    assert parse_annotations(data) == "12"


def test_parse_annotations_maps_a_non_digit_value_when_there_is_no_sign_name() -> None:
    data = AnnotationDataFactory.build(sign_name="", value="engur")

    assert parse_annotations(data) == "LAGAB×HAL"


def test_parse_annotations_falls_back_to_unclear_sign_on_an_unknown_value() -> None:
    data = AnnotationDataFactory.build(sign_name="", value="not-a-known-sign")

    assert parse_annotations(data) == AnnotationValueType.UnclearSign.name


def test_sign_to_sign_ground_truth_returns_the_matched_sign() -> None:
    data = AnnotationDataFactory.build(
        type=AnnotationValueType.HAS_SIGN, sign_name="NUN", value="nun"
    )

    assert sign_to_sign_ground_truth(data) == "NUN"


def test_prepare_annotations_filters_by_type() -> None:
    kept = AnnotationFactory.build(
        geometry=GeometryFactory.build(width=10.0, height=10.0),
        data=AnnotationDataFactory.build(
            type=AnnotationValueType.HAS_SIGN, sign_name="NUN", value="nun"
        ),
    )
    filtered = AnnotationFactory.build(
        geometry=GeometryFactory.build(width=10.0, height=10.0),
        data=AnnotationDataFactory.build(type=AnnotationValueType.BLANK),
    )
    annotations = AnnotationsFactory.build(annotations=(kept, filtered))

    bounding_boxes, signs = prepare_annotations(
        annotations, 100, 100, to_filter=[AnnotationValueType.BLANK]
    )

    assert signs == ["NUN"]
    assert len(bounding_boxes) == 1


def test_write_annotations_rejects_mismatched_lengths(tmp_path) -> None:
    annotations = AnnotationsFactory.build(
        annotations=(
            AnnotationFactory.build(
                geometry=GeometryFactory.build(width=10.0, height=10.0),
                data=AnnotationDataFactory.build(
                    type=AnnotationValueType.HAS_SIGN, sign_name="NUN", value="nun"
                ),
            ),
        )
    )
    bounding_boxes, _ = prepare_annotations(annotations, 100, 100)

    with pytest.raises(ValueError, match="Bounding boxes and signs must match."):
        write_annotations(tmp_path / "gt.txt", bounding_boxes, [])


def test_create_directory_creates_a_missing_directory(tmp_path) -> None:
    target = tmp_path / "annotations"

    create_directory(str(target))

    assert target.is_dir()


def test_create_directory_replaces_an_existing_directory(tmp_path) -> None:
    target = tmp_path / "annotations"
    target.mkdir()
    (target / "stale.txt").write_text("stale")

    create_directory(str(target))

    assert target.is_dir()
    assert list(target.iterdir()) == []
