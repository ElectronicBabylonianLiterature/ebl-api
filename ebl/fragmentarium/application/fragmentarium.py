from typing import Dict, List, Sequence
from ebl.common.domain.scopes import Scope

from ebl.fragmentarium.application.fragment_repository import FragmentRepository
from ebl.fragmentarium.domain.fragment import Fragment
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

    def find_needs_revision(
        self, user_scopes: Sequence[Scope] = ()
    ) -> List[FragmentInfo]:
        return self._repository.query_by_transliterated_not_revised_by_other(
            user_scopes
        )

    def create(self, fragment: Fragment, sort_key=None) -> str:
        return self._repository.create(fragment, sort_key=sort_key)
