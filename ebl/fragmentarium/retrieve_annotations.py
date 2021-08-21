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
from ebl.fragmentarium.domain.annotation import Annotations, Annotation


@attr.attrs(auto_attribs=True, frozen=True)
class Point:
    x: float
    y: float


@attr.attrs(auto_attribs=True, frozen=True)
class BBox:
    top_left: Point
    top_right: Point
    bottom_right: Point
    bottom_left: Point

    @staticmethod
    def from_geometry(geometry, x_shape, y_shape) -> "BBox":
        new_x = int(round(geometry.x / 100 * x_shape))
        new_y = int(round(geometry.y / 100 * y_shape))
        new_width = int(round(geometry.width / 100 * x_shape))
        new_height = int(round(geometry.height / 100 * y_shape))
        return BBox.from_rectange(new_x, new_y, new_width, new_height)

    @staticmethod
    def from_rectange(x: float, y: float, width: float, height: float) -> "BBox":
        return BBox(
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


def convert_bboxes(
    x_shape: int, y_shape: int, annotations: Sequence[Annotation]
) -> Sequence[BBox]:
    return tuple(
        [
            BBox.from_geometry(annotation.geometry, x_shape, y_shape)
            for annotation in annotations
        ]
    )


def create_annotations(
    annotation_collection: Sequence[Annotations],
    output_folder_annotations: str,
    output_folder_images: str,
    context: Context,
) -> None:
    """
    Original format from react-annotation tool is bottom left vertex and height and
    width values between 0 - 100 relative to image size.
    We get image size to calculate absolute coordinates.
    """
    for counter, single_annotation in enumerate(annotation_collection):
        fragment_number = single_annotation.fragment_number

        image_filename = f"{fragment_number}.jpg"
        fragment_image = context.photo_repository.query_by_file_name(image_filename)
        image_bytes = fragment_image.read()
        image = Image.open(BytesIO(image_bytes), mode="r")
        image.save(join(output_folder_images, image_filename))

        bboxes = convert_bboxes(
            image.size[0], image.size[1], single_annotation.annotations
        )
        write_annotations(
            output_folder_annotations, f"gt_{fragment_number}.txt", bboxes
        )
        print(
            "{:>20}".format(f"{fragment_number}"),
            "{:>4}".format(f" {counter} of"),
            "{:>4}".format(len(annotation_collection)),
        )


def write_annotations(
    output_folder_annotations: str, file_name: str, bboxes: Sequence[BBox]
) -> None:
    txt_file = join(output_folder_annotations, file_name)
    with open(txt_file, "w+") as file:
        for bbox in bboxes:
            vertices = ",".join(map(str, bbox.to_tuple_counterclockwise()))
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
        annotation_collection, args.output_annotations, args.output_imgs, context
    )
    print("Done")
