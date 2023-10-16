import argparse
import json
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
            if annotation_data.sign_name.islower():
                return MANUEL_FIX[annotation_data.sign_name]
            else:
                return annotation_data.sign_name
        else:
            if annotation_data.value.isdigit():
                return annotation_data.value
            else:
                return MANUEL_FIX[annotation_data.value]
    except (KeyError, AttributeError) as e:
        print(e)
        print(annotation_data)
        return AnnotationValueType.UnclearSign.name


def sign_to_sign_ground_truth(annotation_data: AnnotationData) -> str:
    sign_ground_truth = match(annotation_data)
    if (
        sign_ground_truth == ""
        or sign_ground_truth == "?"
        or sign_ground_truth.islower()
    ):
        raise ValueError(
            f"AnnotationData with id: '{annotation_data.id}', "
            f"value: '{annotation_data.value}' ",
            f"sign: '{annotation_data.sign_name}' and "
            f"type: '{annotation_data.type.value}' "
            f"results in empty ground truth label",
        )
    return sign_ground_truth


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
    """
    # for detection finished fragments are filtered
    python3 ebl/fragmentarium/annotations/prepare_annotations.py -f
    # for classification
    python3 ebl/fragmentarium/annotations/prepare_annotations.py -c
    """
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
    parser.add_argument(
        "-f",
        "--filter",
        action="store_true",
        help="filter finished Fragments from ./annotations.json",
    )
    parser.add_argument(
        "-c",
        "--classification",
        action="store_true",
        help="Get Signs for detection or classification",
    )
    args = parser.parse_args()

    if None not in (args.output_annotations, args.output_imgs):
        raise argparse.ArgumentError(
            None, message="Either specify both argument options or none at all"
        )

    if args.output_annotations is None and args.output_imgs is None:
        create_directory("annotations")
        create_directory("annotations/annotations")
        create_directory("annotations/imgs")
        args.output_annotations = "./annotations/annotations"
        args.output_imgs = "./annotations/imgs"

    context = create_context()

    annotation_collection = context.annotations_repository.retrieve_all_non_empty()

    if args.filter:
        print(
            "Already finished Fragments are filtered. Finished"
            "fragments are defined in './annotations.json' file"
        )
        finished_fragments = json.load(open("ebl/fragmentarium/annotations.json"))[
            "finished"
        ]

        annotation_collection = list(
            filter(
                lambda elem: str(elem.fragment_number) in [*finished_fragments],
                annotation_collection,
            )
        )
    if args.classification:
        # For Sign Classification (Bounding Boxes have to be cropped for Image Classification)
        TO_FILTER = [
            AnnotationValueType.RULING_DOLLAR_LINE,
            AnnotationValueType.SURFACE_AT_LINE,
            AnnotationValueType.BLANK,
            AnnotationValueType.ColumnAtLine,
            AnnotationValueType.STRUCT,
        ]
    else:
        # For Sign Detection aka Localized Bounding Boxes (Only Images where bounding boxes
        # are complete can be used in contrast to Classification Task where all existing
        # Bounding Boxes can be used by cropping the Images)
        TO_FILTER = [
            AnnotationValueType.RULING_DOLLAR_LINE,
            AnnotationValueType.ColumnAtLine,
        ]
    print(f"Following Annotation Types are filtered: {TO_FILTER}")

    create_annotations(
        annotation_collection,
        args.output_annotations,
        args.output_imgs,
        context.photo_repository,
        to_filter=TO_FILTER,
    )
    write_fragment_numbers(
        annotation_collection, f"./annotations/Annotations_{date.today()}.txt"
    )
    print("Done")
