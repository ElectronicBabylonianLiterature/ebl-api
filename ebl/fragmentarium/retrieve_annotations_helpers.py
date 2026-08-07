import os
import shutil
from io import BytesIO
from itertools import zip_longest
from os.path import join
from pathlib import Path
from typing import Sequence, Union, Tuple

from PIL import Image

from ebl.files.application.file_repository import FileRepository
from ebl.fragmentarium.domain.annotation import (
    Annotations,
    BoundingBox,
    Annotation,
    AnnotationValueType,
    AnnotationData,
)


MINIMUM_BOUNDING_BOX_SIZE = 0.3


def filter_empty_annotation(annotation: Annotation) -> bool:
    sizes = annotation.geometry.width, annotation.geometry.height
    if any(size < MINIMUM_BOUNDING_BOX_SIZE for size in sizes):
        print(
            f"AnnotationData with id: '{annotation.data.id}' has bounding box smaller "
            f"than minimum size"
        )
        return False
    else:
        return True


def filter_annotation(annotation: Annotation, to_filter) -> bool:
    return annotation.data.type not in to_filter and filter_empty_annotation(annotation)


def match(annotation_data: AnnotationData) -> str:
    type = annotation_data.type
    if type == AnnotationValueType.SURFACE_AT_LINE:
        return AnnotationValueType.SURFACE_AT_LINE.name
    if type == AnnotationValueType.BLANK:
        return AnnotationValueType.BLANK.name
    if type == AnnotationValueType.ColumnAtLine:
        return AnnotationValueType.ColumnAtLine.name
    if type == AnnotationValueType.STRUCT:
        return AnnotationValueType.STRUCT.name
    if type == AnnotationValueType.UnclearSign:
        return AnnotationValueType.UnclearSign.name
    if type == AnnotationValueType.PARTIALLY_BROKEN:
        return f"{parse_annotations(annotation_data)}?"
    return parse_annotations(annotation_data)


def parse_annotations(annotation_data: AnnotationData) -> str:
    MANUEL_FIX = {
        "ni": "NI",
        "pa": "PA",
        "šam": "U₂",
        "ti": "TI",
        "li": "LI",
        "NUN": "NUN",
        "ŠU": "ŠU",
        "GUR": "GUR",
        "engur": "LAGAB×HAL",
        "BE": "BAD",
        "NA": "NA",
    }
    try:
        if annotation_data.sign_name != "":
            return (
                MANUEL_FIX[annotation_data.sign_name]
                if annotation_data.sign_name.islower()
                else annotation_data.sign_name
            )
        if annotation_data.value.isdigit():
            return annotation_data.value
        else:
            return MANUEL_FIX[annotation_data.value]
    except (KeyError, AttributeError) as e:
        print(e)
        print(annotation_data)
        return AnnotationValueType.UnclearSign.name


def sign_to_sign_ground_truth(annotation_data: AnnotationData) -> str:
    return match(annotation_data)


def prepare_annotations(
    annotation: Annotations,
    image_width: int,
    image_height: int,
    to_filter: Sequence[AnnotationValueType] = (),
) -> Tuple[Sequence[BoundingBox], Sequence[str]]:
    annotations_with_signs = list(
        filter(lambda x: filter_annotation(x, to_filter), annotation.annotations)
    )

    bounding_boxes = BoundingBox.from_annotations(
        image_width, image_height, annotations_with_signs
    )
    signs = [
        sign_to_sign_ground_truth(annotation.data)
        for annotation in annotations_with_signs
    ]

    return bounding_boxes, signs


def create_annotations(
    annotation_collection: Sequence[Annotations],
    output_folder_annotations: str,
    output_folder_images: str,
    photo_repository: FileRepository,
    to_filter: Sequence[AnnotationValueType] = (),
) -> None:
    for counter, single_annotation in enumerate(annotation_collection):
        fragment_number = single_annotation.fragment_number

        image_filename = f"{fragment_number}.jpg"
        fragment_image = photo_repository.query_by_file_name(image_filename)
        image_bytes = fragment_image.read()
        image = Image.open(BytesIO(image_bytes), mode="r")
        image.save(join(output_folder_images, image_filename))

        bounding_boxes, signs = prepare_annotations(
            single_annotation, image.size[0], image.size[1], to_filter
        )
        write_annotations(
            join(output_folder_annotations, f"gt_{fragment_number}.txt"),
            bounding_boxes,
            signs,
        )
        print(
            "{:>20}".format(f"{fragment_number}"),
            "{:>4}".format(f" {counter + 1} of"),
            "{:>4}".format(len(annotation_collection)),
        )


def write_annotations(
    path: Union[str, Path], bounding_boxes: Sequence[BoundingBox], signs: Sequence[str]
) -> None:
    with open(path, "w+") as file:
        for bounding_box, sign in zip_longest(bounding_boxes, signs):
            if bounding_box is None or sign is None:
                raise ValueError("Bounding boxes and signs must match.")
            rectangle_attributes = [
                str(int(rectangle_attribute))
                for rectangle_attribute in bounding_box.to_list()
            ]
            file.write(",".join(rectangle_attributes) + f",{sign}" + "\n")


def create_directory(path: str) -> None:
    if os.path.exists(path):
        shutil.rmtree(path)
    os.makedirs(path)


def write_fragment_numbers(
    annotation_collection: Sequence[Annotations], path: Union[str, Path]
) -> None:
    with open(path, "w+") as file:
        file.write(f"Total of {len(annotation_collection)} Annotations\n")
        for annotation in annotation_collection:
            file.write(f"{annotation.fragment_number}\n")
