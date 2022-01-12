import base64
import io
from io import BytesIO
from typing import Sequence, NewType, List, Tuple

import attr
import pydash
from singledispatchmethod import singledispatchmethod
from PIL import Image

from ebl.files.application.file_repository import FileRepository
from ebl.fragmentarium.application.annotations_repository import AnnotationsRepository
from ebl.fragmentarium.application.fragment_repository import FragmentRepository
from ebl.fragmentarium.domain.annotation import BoundingBox, Annotation
from ebl.fragmentarium.domain.museum_number import MuseumNumber
from ebl.transliteration.domain.at_line import ObjectAtLine, SurfaceAtLine, ColumnAtLine
from ebl.transliteration.domain.line import Line
from ebl.transliteration.domain.line_label import LineLabel
from ebl.transliteration.domain.text_line import TextLine

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

    @singledispatchmethod
    def _calculate_label_by_type(
        self, line: Line, label: LineLabel, lines: Sequence[Line]
    ):
        return label, lines

    @_calculate_label_by_type.register(TextLine)
    def _(self, line: TextLine, label: LineLabel, lines: Sequence[Line]):
        return label, [*lines, [label.set_line_number(line.line_number), line]]

    @_calculate_label_by_type.register(ObjectAtLine)
    def _(self, line: ObjectAtLine, label: LineLabel, lines: Sequence[Line]):
        return label.set_object(line.label), lines

    @_calculate_label_by_type.register(SurfaceAtLine)
    def _(self, line: SurfaceAtLine, label: LineLabel, lines: Sequence[Line]):
        return label.set_surface(line.surface_label), lines

    @_calculate_label_by_type.register(ColumnAtLine)
    def _(self, line: ColumnAtLine, label: LineLabel, lines: Sequence[Line]):
        return label.set_column(line.column_label), lines

    def _calculate_label(self, total: Tuple[LineLabel, Sequence[Line]], line: Line):
        return self._calculate_label_by_type(line, total[0], total[1])

    def _extract_label(
        self, line_number: int, labels_with_lines: List[Tuple[LineLabel, Line]]
    ) -> str:
        return next(
            (
                label.abbreviation
                for label, _ in labels_with_lines
                if label.is_line_number(line_number)
            ),
            "",
        )

    def _get_label_of_line(self, line_number: int, lines: Sequence[Line]) -> str:
        init_value = LineLabel(None, None, None, None), []
        labels_with_lines = pydash.reduce_(lines, self._calculate_label, init_value)[1]
        return self._extract_label(line_number, labels_with_lines)

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

    def _cropped_image_from_annotations(
        self, fragment_number: MuseumNumber, annotations: Sequence[Annotation]
    ):
        cropped_annotations = []
        for annotation in annotations:
            fragment = self._fragments_repository.query_by_museum_number(
                fragment_number
            )
            script = fragment.script
            label = self._get_label_of_line(
                annotation.data.path[0], fragment.text.lines
            )
            cropped_image = self._cropped_image_from_annotation(
                annotation, fragment_number
            )
            cropped_annotations.append(
                CroppedAnnotation(cropped_image, fragment_number, script, label)
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
