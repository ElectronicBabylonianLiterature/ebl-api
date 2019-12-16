from ebl.fragmentarium.application.annotation_repository import AnnotationRepository
from ebl.fragmentarium.domain.annotation import Annotations
from ebl.fragmentarium.domain.fragment import FragmentNumber


class AnnotationService:
    def __init__(self, repository: AnnotationRepository):
        self._repository = repository

    def find(self, fragment_number: FragmentNumber) -> Annotations:
        return self._repository.query_by_fragment_number(fragment_number)

    def update(self, annotations: Annotations) -> Annotations:
        self._repository.create_or_update(annotations)
        return annotations
