from typing import List

from ebl.fragmentarium.application.fragment_repository import \
    FragmentRepository
from ebl.fragmentarium.domain.fragment import Fragment, FragmentNumber
from ebl.fragmentarium.domain.fragment_info import FragmentInfo
from ebl.fragmentarium.domain.transliteration_query import \
    TransliterationQuery


class FragmentFinder:

    def __init__(self,
                 repository: FragmentRepository,
                 dictionary):

        self._repository = repository
        self._dictionary = dictionary

    def find(self, number: FragmentNumber) -> Fragment:
        return self._repository.query_by_fragment_number(number)

    def search(self, number: str) -> List[FragmentInfo]:
        return list(map(
            FragmentInfo.of,
            self._repository.query_by_fragment_cdli_or_accession_number(
                number
            )
        ))

    def search_transliteration(
            self, query: TransliterationQuery
    ) -> List[FragmentInfo]:
        return [
            FragmentInfo.of(fragment, query.get_matching_lines(fragment))
            for fragment
            in self._repository.query_by_transliteration(query)
        ]

    def find_random(self) -> List[FragmentInfo]:
        return list(map(
            FragmentInfo.of,
            self._repository.query_random_by_transliterated()
        ))

    def find_interesting(self) -> List[FragmentInfo]:
        return list(map(
            FragmentInfo.of,
            self._repository.query_by_kuyunjik_not_transliterated_joined_or_published()  # noqa: F401
        ))

    def folio_pager(self,
                    folio_name: str,
                    folio_number: str,
                    number: FragmentNumber) -> dict:
        return self._repository.query_next_and_previous_folio(folio_name,
                                                              folio_number,
                                                              number)

    def find_lemmas(self, word: str) -> List[List[dict]]:
        return [
            [
                self._dictionary.find(unique_lemma)
                for unique_lemma
                in result
            ]
            for result
            in self._repository.query_lemmas(word)
        ]
