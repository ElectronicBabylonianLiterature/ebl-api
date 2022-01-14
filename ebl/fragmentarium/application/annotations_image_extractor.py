import base64
import io
from singledispatchmethod import singledispatchmethod
from io import BytesIO
from typing import Sequence, NewType

import attr
from PIL import Image

from ebl.files.application.file_repository import FileRepository
from ebl.fragmentarium.application.annotations_repository import AnnotationsRepository
from ebl.fragmentarium.application.fragment_repository import FragmentRepository
from ebl.fragmentarium.domain.annotation import BoundingBox, Annotation
from ebl.fragmentarium.domain.museum_number import MuseumNumber
from ebl.transliteration.domain.line_label import LineLabel
from ebl.transliteration.domain.line_number import (
    AbstractLineNumber,
    LineNumber,
    LineNumberRange,
)

Base64 = NewType("Base64", str)


@attr.attrs(auto_attribs=True, frozen=True)
class CroppedAnnotation:
    image: Base64
    fragment_number: MuseumNumber
    script: str
    label: str


class AnnotationImageExtractor:
    def __init__(
        self,
        fragment_repository: FragmentRepository,
        annotations_repository: AnnotationsRepository,
        photos_repository: FileRepository,
    ):
        self._fragments_repository = fragment_repository
        self._annotations_repository = annotations_repository
        self._photos_repository = photos_repository

    def _format_label(self, label: LineLabel) -> str:
        line_number = label.line_number
        column = label.column
        surface = label.surface
        object = label.object
        line_atf = line_number.atf if line_number else ""
        column_abbr = column.abbreviation if column else ""
        surface_abbr = surface.abbreviation if surface else ""
        object_abbr = object.abbreviation if object else ""
        return " ".join(
            filter(
                bool,
                [column_abbr, surface_abbr, object_abbr, line_atf.replace(".", "")],
            )
        )

    def _cropped_image_from_annotation(
        self, annotation: Annotation, fragment_number: MuseumNumber
    ) -> Base64:
        fragment_image = self._photos_repository.query_by_file_name(
            f"{fragment_number}.jpg"
        )
        image_bytes = fragment_image.read()
        image = Image.open(BytesIO(image_bytes), mode="r")
        bounding_boxes = BoundingBox.from_annotations(
            image.size[0], image.size[1], [annotation]
        )[0]
        area = (
            bounding_boxes.top_left_x,
            bounding_boxes.top_left_y,
            bounding_boxes.top_left_x + bounding_boxes.width,
            bounding_boxes.top_left_y + bounding_boxes.height,
        )
        cropped_image = image.crop(area)
        buf = io.BytesIO()
        cropped_image.save(buf, format="PNG")
        return Base64(base64.b64encode(buf.getvalue()).decode("utf-8"))

    @singledispatchmethod
    def _is_matching_number(self, line_number: AbstractLineNumber, number: int) -> bool:
        raise ValueError("No default for overloading")

    @_is_matching_number.register(LineNumber)
    def _(self, line_number: LineNumber, number: int):
        return number == line_number.number

    @_is_matching_number.register(LineNumberRange)
    def _(self, line_number: LineNumberRange, number: int):
        return line_number.start.number <= number <= line_number.end.number

    def _cropped_image_from_annotations(
        self, fragment_number: MuseumNumber, annotations: Sequence[Annotation]
    ) -> Sequence[CroppedAnnotation]:
        cropped_annotations = []
        for annotation in annotations:
            fragment = self._fragments_repository.query_by_museum_number(
                fragment_number
            )
            script = fragment.script
            labels = fragment.text.labels
            label = next(
                (
                    label
                    for label in labels
                    if self._is_matching_number(
                        label.line_number, annotation.data.path[0]
                    )
                ),
                None,
            )

            cropped_image = self._cropped_image_from_annotation(
                annotation, fragment_number
            )
            cropped_annotations.append(
                CroppedAnnotation(
                    cropped_image,
                    fragment_number,
                    script,
                    self._format_label(label) if label else "",
                )
            )
        return cropped_annotations

    def cropped_images_from_sign(self, sign: str) -> Sequence[CroppedAnnotation]:
        annotations = self._annotations_repository.find_by_sign(sign)
        cropped_annotations = []
        for single_annotation in annotations:
            fragment_number = single_annotation.fragment_number
            cropped_annotations.extend(
                self._cropped_image_from_annotations(
                    fragment_number, single_annotation.annotations
                )
            )
        return cropped_annotations
