import base64
import io
from io import BytesIO
from typing import Tuple, Sequence

import attr
import bson.objectid
from PIL import Image
from functools import singledispatchmethod

from ebl.changelog import Changelog
from ebl.ebl_ai_client import EblAiClient
from ebl.files.application.file_repository import FileRepository
from ebl.fragmentarium.application.annotations_repository import AnnotationsRepository
from ebl.fragmentarium.application.annotations_schema import AnnotationsSchema
from ebl.fragmentarium.application.cropped_sign_image import Base64, CroppedSign
from ebl.fragmentarium.application.fragment_repository import FragmentRepository
from ebl.fragmentarium.application.cropped_sign_images_repository import (
    CroppedSignImage,
    CroppedSignImagesRepository,
)
from ebl.fragmentarium.domain.annotation import (
    Annotations,
    Annotation,
    BoundingBox,
    AnnotationValueType,
)
from ebl.fragmentarium.domain.museum_number import MuseumNumber
from ebl.transliteration.domain.line_label import LineLabel
from ebl.transliteration.domain.line_number import (
    LineNumber,
    LineNumberRange,
    AbstractLineNumber,
)
from ebl.users.domain.user import User


@attr.attrs(auto_attribs=True, frozen=True)
class AnnotationsService:
    _ebl_ai_client: EblAiClient
    _annotations_repository: AnnotationsRepository
    _photo_repository: FileRepository
    _changelog: Changelog
    _fragments_repository: FragmentRepository
    _photos_repository: FileRepository
    _cropped_sign_images_repository: CroppedSignImagesRepository

    def generate_annotations(
        self, number: MuseumNumber, threshold: float = 0.3
    ) -> Annotations:
        fragment_image = self._photo_repository.query_by_file_name(f"{number}.jpg")
        return self._ebl_ai_client.generate_annotations(
            number, fragment_image, threshold
        )

    def find(self, number: MuseumNumber) -> Annotations:
        return self._annotations_repository.query_by_museum_number(number)

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
        self, annotation: Annotation, image: Image.Image
    ) -> Base64:
        bounding_box = BoundingBox.from_annotations(
            image.size[0], image.size[1], [annotation]
        )[0]
        area = (
            bounding_box.top_left_x,
            bounding_box.top_left_y,
            bounding_box.top_left_x + bounding_box.width,
            bounding_box.top_left_y + bounding_box.height,
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

    @_is_matching_number.register(LineNumberRange)  # pyre-ignore[56]
    def _(self, line_number: LineNumberRange, number: int):
        return line_number.start.number <= number <= line_number.end.number

    def _cropped_image_from_annotations(
        self, annotations: Annotations
    ) -> Tuple[Annotations, Sequence[CroppedSignImage]]:
        cropped_sign_images = []
        cropped_annotations = []
        fragment = self._fragments_repository.query_by_museum_number(
            annotations.fragment_number
        )
        fragment_image = self._photos_repository.query_by_file_name(
            f"{annotations.fragment_number}.jpg"
        )
        image_bytes = fragment_image.read()
        image = Image.open(BytesIO(image_bytes), mode="r")
        for annotation in annotations.annotations:
            script = fragment.script
            labels = fragment.text.labels
            label = (
                next(
                    (
                        label
                        for label in labels
                        if self._is_matching_number(
                            label.line_number, annotation.data.path[0]
                        )
                    ),
                    None,
                )
                if annotation.data.type != AnnotationValueType.BLANK
                else None
            )
            cropped_image_base64 = self._cropped_image_from_annotation(
                annotation, image
            )
            image_id = str(bson.ObjectId())
            cropped_sign_images.append(CroppedSignImage(image_id, cropped_image_base64))
            cropped_annotations.append(
                attr.evolve(
                    annotation,
                    cropped_sign=CroppedSign(
                        image_id,
                        script,
                        self._format_label(label) if label else "",
                    ),
                )
            )
        return (
            attr.evolve(annotations, annotations=cropped_annotations),
            cropped_sign_images,
        )

    def update(self, annotations: Annotations, user: User) -> Annotations:
        old_annotations = self._annotations_repository.query_by_museum_number(
            annotations.fragment_number
        )
        _id = str(annotations.fragment_number)
        schema = AnnotationsSchema()
        (
            annotations_with_image_ids,
            cropped_sign_images,
        ) = self._cropped_image_from_annotations(annotations)
        self._annotations_repository.create_or_update(annotations_with_image_ids)
        self._cropped_sign_images_repository.create_many(cropped_sign_images)
        self._changelog.create(
            "annotations",
            user.profile,
            {"_id": _id, **schema.dump(old_annotations)},
            {"_id": _id, **schema.dump(annotations_with_image_ids)},
        )
        return annotations_with_image_ids
