import argparse
import os
import shutil
from io import BytesIO
from os.path import join
from pathlib import Path
from typing import Sequence, Union

from PIL import Image

from ebl.app import create_context
from ebl.files.application.file_repository import FileRepository
from ebl.fragmentarium.domain.annotation import Annotations, BoundingBox


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

        bounding_boxes = BoundingBox.from_annotations(
            image.size[0], image.size[1], single_annotation.annotations
        )
        signs = [
            annotations.data.sign_name for annotations in single_annotation.annotations
        ]

        if len(signs) != len(bounding_boxes):
            raise ValueError(
                f"Number of Bounding Boxes doesn't match number of "
                f"Signs on Annotation: {fragment_number}"
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
            file.write(",".join(rectangle_attributes) + f" {sign}" + "\n")


def create_directory(path: str) -> None:
    if os.path.exists(path):
        shutil.rmtree(path)
    os.makedirs(path)


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
    annotation_collection = context.annotations_repository.retrieve_all()
    create_annotations(
        annotation_collection,
        args.output_annotations,
        args.output_imgs,
        context.photo_repository,
    )
    print("Done")
