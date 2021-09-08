import argparse
import os
import shutil
from io import BytesIO
from os.path import join
from typing import Sequence, Tuple

import attr
from PIL import Image

from ebl.app import create_context
from ebl.context import Context
from ebl.files.application.file_repository import FileRepository
from ebl.fragmentarium.domain.annotation import Annotations, Annotation


@attr.attrs(auto_attribs=True, frozen=True)
class Point:
    x: float
    y: float


@attr.attrs(auto_attribs=True, frozen=True)
class BoundingBox:
    top_left: Point
    top_right: Point
    bottom_right: Point
    bottom_left: Point

    @staticmethod
    def from_relative_to_absolute_coordinates(
        relative_x,
        relative_y,
        relative_width,
        relative_height,
        image_width,
        image_height,
    ) -> "BoundingBox":
        absolute_x = int(round(relative_x / 100 * image_width))
        absolute_y = int(round(relative_y / 100 * image_height))
        absolute_width = int(round(relative_width / 100 * image_width))
        absolute_height = int(round(relative_height / 100 * image_height))
        return BoundingBox.from_rectange(
            absolute_x, absolute_y, absolute_width, absolute_height
        )

    @staticmethod
    def from_rectange(x: float, y: float, width: float, height: float) -> "BoundingBox":
        return BoundingBox(
            Point(x, y),
            Point(x + width, y),
            Point(x + width, y + height),
            Point(x, y + height),
        )

    def to_tuple_counterclockwise(
        self
    ) -> Tuple[float, float, float, float, float, float, float, float]:
        return (
            self.top_left.x,
            self.top_left.y,
            self.top_right.x,
            self.top_right.y,
            self.bottom_right.x,
            self.bottom_right.y,
            self.bottom_left.x,
            self.bottom_right.y,
        )


def convert_to_bounding_boxes(
    image_width: int, image_height: int, annotations: Sequence[Annotation]
) -> Sequence[BoundingBox]:
    return tuple(
        [
            BoundingBox.from_relative_to_absolute_coordinates(
                annotation.geometry.x,
                annotation.geometry.y,
                annotation.geometry.width,
                annotation.geometry.height,
                image_width,
                image_height,
            )
            for annotation in annotations
        ]
    )


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

        bounding_boxes = convert_to_bounding_boxes(
            image.size[0], image.size[1], single_annotation.annotations
        )
        write_annotations(
            output_folder_annotations, f"gt_{fragment_number}.txt", bounding_boxes
        )
        print(
            "{:>20}".format(f"{fragment_number}"),
            "{:>4}".format(f" {counter} of"),
            "{:>4}".format(len(annotation_collection)),
        )


def write_annotations(
    output_folder_annotations: str,
    file_name: str,
    bounding_boxes: Sequence[BoundingBox],
) -> None:
    txt_file = join(output_folder_annotations, file_name)
    with open(txt_file, "w+") as file:
        for bounding_box in bounding_boxes:
            vertices = ",".join(map(str, bounding_box.to_tuple_counterclockwise()))
            file.write(vertices + "\n")


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
        create_directory("annotations")
        create_directory("annotations/annotations")
        create_directory("annotations/imgs")
        args.output_annotations = "annotations/annotations"
        args.output_imgs = "annotations/imgs"

    context = create_context()
    annotation_collection = context.annotations_repository.retrieve_all()
    create_annotations(
        annotation_collection,
        args.output_annotations,
        args.output_imgs,
        context.photo_repository,
    )
    print("Done")
