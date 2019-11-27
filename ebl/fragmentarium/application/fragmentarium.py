from typing import Dict, List

from ebl.fragmentarium.application.fragment_repository import FragmentRepository
from ebl.fragmentarium.domain.fragment import Fragment, FragmentNumber
from ebl.fragmentarium.domain.fragment_info import FragmentInfo


class Fragmentarium:
    def __init__(self, repository: FragmentRepository):

        self._repository = repository

    def statistics(self) -> Dict[str, int]:
        return {
            "transliteratedFragments": (
                self._repository.count_transliterated_fragments()
            ),
            "lines": self._repository.count_lines(),
        }

    def find_latest(self) -> List[FragmentInfo]:
        return list(
            map(
                FragmentInfo.of,
                self._repository.query_by_transliterated_sorted_by_date(),
            )
        )

    def find_needs_revision(self) -> List[FragmentInfo]:
        return self._repository.query_by_transliterated_not_revised_by_other()

    def create(self, fragment: Fragment) -> FragmentNumber:
        return self._repository.create(fragment)
