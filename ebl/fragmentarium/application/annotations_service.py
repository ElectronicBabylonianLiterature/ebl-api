from ebl.fragmentarium.application.annotations_repository import AnnotationsRepository
from ebl.fragmentarium.domain.annotation import Annotations
from ebl.fragmentarium.domain.fragment import FragmentNumber


class AnnotationsService:
    def __init__(self, repository: AnnotationsRepository):
        self._repository = repository

    def find(self, fragment_number: FragmentNumber) -> Annotations:
        return self._repository.query_by_fragment_number(fragment_number)

    def update(self, annotations: Annotations) -> Annotations:
        self._repository.create_or_update(annotations)
        return annotations
