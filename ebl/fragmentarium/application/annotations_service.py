from io import BytesIO
from typing import Callable, List, Mapping, Sequence, Tuple, Type

import attr
from PIL import Image
from marshmallow import EXCLUDE

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
from ebl.fragmentarium.application.fragment_schema import FragmentSchema
from ebl.fragmentarium.domain.annotation import (
    Annotations,
    AnnotationValueType,
)
from ebl.transliteration.domain.at_line import ColumnAtLine, ObjectAtLine, SurfaceAtLine
from ebl.transliteration.domain.line import Line
from ebl.transliteration.domain.line_label import LineLabel
from ebl.transliteration.domain.museum_number import MuseumNumber
from ebl.transliteration.domain.note_line import NoteLine
from ebl.transliteration.domain.text_line import TextLine
from ebl.users.domain.user import User

Image.MAX_IMAGE_PIXELS = None  # pyre-ignore[9]


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


    def _cropped_image_from_annotations_helper(
        self,
        annotations: Annotations,
        image: Image.Image,
    ) -> Tuple[Annotations, Sequence[CroppedSignImage]]:
        cropped_sign_images = []
        updated_cropped_annotations = []

        for annotation in annotations.annotations:
            cropped_image = annotation.crop_image(image)
            cropped_sign_image = CroppedSignImage.create(cropped_image)
            cropped_sign_images.append(cropped_sign_image)

            updated_cropped_annotation = attr.evolve(
                annotation,
                cropped_sign=CroppedSign(cropped_sign_image.image_id, annotation.data),
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
            annotations, image
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

        len(cropped_sign_images) and self._cropped_sign_images_repository.create_many(
            cropped_sign_images
        )

        self._changelog.create(
            "annotations",
            user.profile,
            {"_id": _id, **schema.dump(old_annotations)},
            {"_id": _id, **schema.dump(annotations_with_image_ids)},
        )
        return annotations_with_image_ids

    def _migrate(
            self, annotations: Annotations
    ) -> Annotations:
        fragment = self._fragments_repository.query_by_museum_number(
            annotations.fragment_number
        )
        if str(fragment.number) == "BM.34314":
            fragment = self._fragments_repository._fragments.find_one({"_id": "BM.34313"})
            fragment = FragmentSchema(unknown=EXCLUDE).load(fragment)
            labels = calc_labels(fragment.text.lines)
        else:
            labels = calc_labels(fragment.text.lines)

        updated_cropped_annotations = []
        for annotation in annotations.annotations:
            if len(annotation.data.path) and len(labels):
                label = labels[annotation.data.path[0]][0].formatted_label
                if annotation.cropped_sign is None:
                    pass
                if annotation.cropped_sign is not None and annotation.cropped_sign.label != label:
                    print(
                        f"{fragment.number} -- {annotation.data.sign_name} --- {annotation.cropped_sign.label}-------{label}")
                    updated_cropped_annotation = attr.evolve(
                        annotation,
                        cropped_sign=CroppedSign(
                            annotation.cropped_sign.image_id,
                            label,
                        ),
                    )
                    updated_cropped_annotations.append(updated_cropped_annotation)
                else:
                    updated_cropped_annotations.append(annotation)
        return attr.evolve(annotations, annotations=updated_cropped_annotations)


    def migrate(self, annotations: Annotations) -> Annotations:
        annotations_with_image_ids = self._migrate(annotations)
        self._annotations_repository.create_or_update(annotations_with_image_ids)
        return annotations_with_image_ids


def calc_labels(lines) -> Sequence[LineLabel]:
    current: LineLabel = LineLabel(None, None, None, None)
    labels: List[LineLabel] = []

    handlers: Mapping[
        Type[Line], Callable[[Line], Tuple[LineLabel, List[LineLabel]]]
    ] = {
        TextLine: lambda line: (
            current,
            [*labels, [current.set_line_number(line.line_number), str(type(line))]],
        ),
        ColumnAtLine: lambda line: (current.set_column(line.column_label), [*labels, [current, str(type(line))]]),
        SurfaceAtLine: lambda line: (
            current.set_surface(line.surface_label),
            [*labels, [current, str(type(line))]],
        ),
        ObjectAtLine: lambda line: (current.set_object(line.label), [*labels, [current, str(type(line))]]),
    }

    for line in lines:
        if type(line) in handlers:
            current, labels = handlers[type(line)](line)
        elif type(line) != NoteLine:
            current, labels = current, [*labels, [current, str(type(line))]]
    return labels
