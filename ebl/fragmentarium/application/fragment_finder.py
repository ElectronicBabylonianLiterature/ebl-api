from typing import List

from ebl.fragmentarium.application.fragment_repository import \
    FragmentRepository
from ebl.fragmentarium.domain.fragment import Fragment, FragmentNumber
from ebl.fragmentarium.domain.fragment_info import FragmentInfo


class FragmentFinder:

    def __init__(self,
                 repository: FragmentRepository,
                 dictionary):

        self._repository = repository
        self._dictionary = dictionary

    def find(self, number: FragmentNumber) -> Fragment:
        return self._repository.find(number)

    def search(self, number: str) -> List[FragmentInfo]:
        return list(map(FragmentInfo.of, self._repository.search(number)))

    def find_random(self) -> List[FragmentInfo]:
        return list(map(FragmentInfo.of, self._repository.find_random()))

    def find_interesting(self) -> List[FragmentInfo]:
        return list(map(FragmentInfo.of, self._repository.find_interesting()))

    def folio_pager(self,
                    folio_name: str,
                    folio_number: str,
                    number: FragmentNumber) -> dict:
        return self._repository.folio_pager(folio_name, folio_number, number)

    def find_lemmas(self, word: str) -> List[List[dict]]:
        return [
            [
                self._dictionary.find(unique_lemma)
                for unique_lemma
                in result
            ]
            for result
            in self._repository.find_lemmas(word)
        ]
