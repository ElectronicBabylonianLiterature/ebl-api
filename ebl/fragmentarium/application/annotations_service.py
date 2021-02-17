from ebl.fragmentarium.application.annotations_repository import AnnotationsRepository
from ebl.fragmentarium.application.annotations_schema import AnnotationsSchema
from ebl.fragmentarium.domain.annotation import Annotations
from ebl.fragmentarium.domain.museum_number import MuseumNumber
from ebl.users.domain.user import User


class AnnotationsService:
    def __init__(self, repository: AnnotationsRepository, changelog):
        self._repository = repository
        self._changelog = changelog

    def find(self, number: MuseumNumber) -> Annotations:
        return self._repository.query_by_museum_number(number)

    def update(self, annotations: Annotations, user: User) -> Annotations:
        old_annotations = self._repository.query_by_museum_number(
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
        self._repository.create_or_update(annotations)
        return annotations
