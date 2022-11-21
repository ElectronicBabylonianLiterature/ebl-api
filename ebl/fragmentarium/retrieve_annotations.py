import argparse
import os
import shutil
from datetime import date
from io import BytesIO
from os.path import join
from pathlib import Path
from typing import Sequence, Union, Tuple

from PIL import Image

from ebl.app import create_context
from ebl.files.application.file_repository import FileRepository
from ebl.fragmentarium.domain.annotation import (
    Annotations,
    BoundingBox,
    Annotation,
    AnnotationValueType,
    AnnotationData,
)

MINIMUM_BOUNDING_BOX_SIZE = 0.3
TO_FILTER = [
    AnnotationValueType.RULING_DOLLAR_LINE,
    AnnotationValueType.SURFACE_AT_LINE,
    AnnotationValueType.STRUCT,
]


def filter_empty_annotation(annotation: Annotation) -> bool:
    sizes = annotation.geometry.width, annotation.geometry.height
    if any(filter(lambda x: x < MINIMUM_BOUNDING_BOX_SIZE, sizes)):
        print(
            f"AnnotationData with id: '{annotation.data.id}' has bounding box smaller "
            f"than minimum size"
        )
        return False
    else:
        return True


def filter_annotation_by_type(annotation: Annotation) -> bool:
    return annotation.data.type not in TO_FILTER


def filter_annotation(annotation: Annotation) -> bool:
    return filter_annotation_by_type(annotation) and filter_empty_annotation(annotation)


def handle_blank_annotation_type(annotation_data: AnnotationData) -> str:
    if annotation_data.type == AnnotationValueType.BLANK:
        ground_truth = AnnotationValueType.BLANK.name
    else:
        ground_truth = annotation_data.sign_name or annotation_data.value
    if not ground_truth:
        raise ValueError(
            f"AnnotationData with id: '{annotation_data.id}', "
            f"value: '{annotation_data.value}' "
            f"sign: '{annotation_data.sign_name}' and "
            f"type: '{annotation_data.type.value}' "
            f"results in empty ground truth label"
        )
    return ground_truth


def prepare_annotations(
    annotation: Annotations, image_width: int, image_height: int
) -> Tuple[Sequence[BoundingBox], Sequence[str]]:

    annotations_with_signs = list(filter(filter_annotation, annotation.annotations))

    bounding_boxes = BoundingBox.from_annotations(
        image_width, image_height, annotations_with_signs
    )
    signs = [
        handle_blank_annotation_type(annotation.data)
        for annotation in annotations_with_signs
    ]

    if len(signs) != len(bounding_boxes):
        raise ValueError(
            f"Number of Bounding Boxes doesn't match number of "
            f"Signs on Annotation: {annotation.fragment_number}"
        )
    return bounding_boxes, signs


def create_annotations(
    annotation_collection: Sequence[Annotations],
    output_folder_annotations: str,
    output_folder_images: str,
    photo_repository: FileRepository,
) -> None:
    for counter, single_annotation in enumerate(annotation_collection):
        fragment_number = single_annotation.fragment_number

        image_filename = f"{fragment_number}.jpg"
        fragment_image = photo_repository.query_by_file_name(image_filename)
        image_bytes = fragment_image.read()
        image = Image.open(BytesIO(image_bytes), mode="r")
        image.save(join(output_folder_images, image_filename))

        bounding_boxes, signs = prepare_annotations(
            single_annotation, image.size[0], image.size[1]
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
        for bounding_box, sign in zip(bounding_boxes, signs):
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


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-oa",
        "--output_annotations",
        type=str,
        default=None,
        help="Output Annotations Directory",
    )
    parser.add_argument(
        "-oi", "--output_imgs", type=str, default=None, help="Output Images Directory"
    )
    args = parser.parse_args()

    if None not in (args.output_annotations, args.output_imgs):
        raise argparse.ArgumentError(
            None, message="Either specify both argument options or none at all"
        )

    if args.output_annotations is None and args.output_imgs is None:
        create_directory("./annotations")
        create_directory("./annotations/annotations")
        create_directory("./annotations/imgs")
        args.output_annotations = "./annotations/annotations"
        args.output_imgs = "./annotations/imgs"

    context = create_context()
    print(f"Following Annotation Types are filtered: {TO_FILTER}")
    annotation_collection = context.annotations_repository.retrieve_all_non_empty()
    create_annotations(
        annotation_collection,
        args.output_annotations,
        args.output_imgs,
        context.photo_repository,
    )
    write_fragment_numbers(
        annotation_collection, f"./annotations/Annotations_{date.today()}.txt"
    )
    print("Done")
