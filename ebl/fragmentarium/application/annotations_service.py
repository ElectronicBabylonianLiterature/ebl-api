from io import BytesIO
from typing import Tuple, Sequence

import attr
from PIL import Image

from ebl.changelog import Changelog
from ebl.ebl_ai_client import EblAiClient
from ebl.files.application.file_repository import FileRepository
from ebl.fragmentarium.application.annotations_repository import AnnotationsRepository
from ebl.fragmentarium.application.annotations_schema import AnnotationsSchema
from ebl.fragmentarium.application.cropped_sign_image import CroppedSign
from ebl.fragmentarium.application.cropped_sign_images_repository import (
    CroppedSignImage,
    CroppedSignImagesRepository,
)
from ebl.fragmentarium.application.fragment_repository import FragmentRepository
from ebl.fragmentarium.domain.annotation import (
    Annotations,
    AnnotationValueType,
)

from ebl.transliteration.domain.line_label import LineLabel
from ebl.transliteration.domain.museum_number import MuseumNumber
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

    def _label_by_line_number(
        self, line_number_to_match: int, labels: Sequence[LineLabel]
    ) -> str:
        matching_label = None
        for label in labels:
            label_line_number = label.line_number
            if label_line_number and label_line_number.is_matching_number(
                line_number_to_match
            ):
                matching_label = label
        return matching_label.formatted_label if matching_label else ""

    def _cropped_image_from_annotations_helper(
        self,
        annotations: Annotations,
        image: Image.Image,
        script: str,
        labels: Sequence[LineLabel],
    ) -> Tuple[Annotations, Sequence[CroppedSignImage]]:
        cropped_sign_images = []
        updated_cropped_annotations = []

        for annotation in annotations.annotations:
            label = (
                self._label_by_line_number(annotation.data.path[0], labels)
                if annotation.data.type != AnnotationValueType.BLANK
                else ""
            )
            cropped_image = annotation.crop_image(image)
            cropped_sign_image = CroppedSignImage.create(cropped_image)
            cropped_sign_images.append(cropped_sign_image)

            updated_cropped_annotation = attr.evolve(
                annotation,
                cropped_sign=CroppedSign(
                    cropped_sign_image.image_id,
                    script,
                    label,
                ),
            )
            updated_cropped_annotations.append(updated_cropped_annotation)
        return (
            attr.evolve(annotations, annotations=updated_cropped_annotations),
            cropped_sign_images,
        )

    def _cropped_image_from_annotations(
        self, annotations: Annotations
    ) -> Tuple[Annotations, Sequence[CroppedSignImage]]:
        fragment = self._fragments_repository.query_by_museum_number(
            annotations.fragment_number
        )
        fragment_image = self._photos_repository.query_by_file_name(
            f"{annotations.fragment_number}.jpg"
        )
        image_bytes = fragment_image.read()
        image = Image.open(BytesIO(image_bytes), mode="r")
        return self._cropped_image_from_annotations_helper(
            annotations, image, fragment.script, fragment.text.labels
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
