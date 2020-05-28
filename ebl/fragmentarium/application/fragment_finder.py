from typing import List, Tuple

from ebl.dictionary.application.dictionary import Dictionary
from ebl.files.application.file_repository import File, FileRepository
from ebl.fragmentarium.application.fragment_repository import FragmentRepository
from ebl.fragmentarium.domain.folios import Folio
from ebl.fragmentarium.domain.fragment import Fragment, FragmentNumber
from ebl.fragmentarium.domain.fragment_info import FragmentInfo
from ebl.fragmentarium.domain.transliteration_query import TransliterationQuery


class FragmentFinder:
    def __init__(
        self,
        repository: FragmentRepository,
        dictionary: Dictionary,
        photos: FileRepository,
        folios: FileRepository,
    ):

        self._repository = repository
        self._dictionary = dictionary
        self._photos = photos
        self._folios = folios

    def find(self, number: FragmentNumber) -> Tuple[Fragment, bool]:
        return (
            self._repository.query_by_fragment_number(number),
            self._photos.query_if_file_exists(f"{number}.jpg"),
        )

    def search(self, number: str) -> List[FragmentInfo]:
        return list(
            map(
                FragmentInfo.of,
                self._repository.query_by_fragment_cdli_or_accession_number(number),
            )
        )

    def search_references(self, reference_id, reference_pages: str) -> List[FragmentInfo]:
        return list(
            map(
                FragmentInfo.of,
                self._repository.query_by_id_and_page_in_references(
                    reference_id,
                    reference_pages
                ),
            )
        )

    def search_transliteration(self, query: TransliterationQuery) -> List[FragmentInfo]:
        if query.is_empty():
            return []
        else:
            return [
                FragmentInfo.of(fragment, query.get_matching_lines(fragment))
                for fragment in self._repository.query_by_transliteration(query)
            ]

    def find_random(self) -> List[FragmentInfo]:
        return list(
            map(FragmentInfo.of, self._repository.query_random_by_transliterated(),)
        )

    def find_interesting(self) -> List[FragmentInfo]:
        return list(
            map(FragmentInfo.of, (self._repository.query_path_of_the_pioneers()),)
        )

    def folio_pager(
        self, folio_name: str, folio_number: str, number: FragmentNumber
    ) -> dict:
        return self._repository.query_next_and_previous_folio(
            folio_name, folio_number, number
        )

    def fragment_pager(self, number: FragmentNumber) -> dict:
        return self._repository.query_next_and_previous_fragment(number)

    def find_lemmas(self, word: str) -> List[List[dict]]:
        return [
            [self._dictionary.find(unique_lemma) for unique_lemma in result]
            for result in self._repository.query_lemmas(word)
        ]

    def find_folio(self, folio: Folio) -> File:
        file_name = folio.file_name
        return self._folios.query_by_file_name(file_name)

    def find_photo(self, number: FragmentNumber) -> File:
        file_name = f"{number}.jpg"
        return self._photos.query_by_file_name(file_name)
