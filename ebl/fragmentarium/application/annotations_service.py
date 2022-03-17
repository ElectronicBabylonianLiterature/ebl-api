from ebl.changelog import Changelog
from ebl.ebl_ai_client import EblAiClient
import attr
from ebl.files.application.file_repository import FileRepository
from ebl.fragmentarium.application.annotations_repository import AnnotationsRepository
from ebl.fragmentarium.application.annotations_schema import AnnotationsSchema
from ebl.fragmentarium.domain.annotation import Annotations
from ebl.transliteration.domain.museum_number import MuseumNumber
from ebl.users.domain.user import User


@attr.attrs(auto_attribs=True, frozen=True)
class AnnotationsService:
    _ebl_ai_client: EblAiClient
    _annotations_repository: AnnotationsRepository
    _photo_repository: FileRepository
    _changelog: Changelog

    def generate_annotations(
        self, number: MuseumNumber, threshold: float = 0.3
    ) -> Annotations:
        fragment_image = self._photo_repository.query_by_file_name(f"{number}.jpg")
        return self._ebl_ai_client.generate_annotations(
            number, fragment_image, threshold
        )

    def find(self, number: MuseumNumber) -> Annotations:
        return self._annotations_repository.query_by_museum_number(number)

    def update(self, annotations: Annotations, user: User) -> Annotations:
        old_annotations = self._annotations_repository.query_by_museum_number(
            annotations.fragment_number
        )
        _id = str(annotations.fragment_number)
        schema = AnnotationsSchema()
        self._changelog.create(
            "annotations",
            user.profile,
            {"_id": _id, **schema.dump(old_annotations)},
            {"_id": _id, **schema.dump(annotations)},
        )
        self._annotations_repository.create_or_update(annotations)
        return annotations
