from typing import List, Tuple

from ebl.bibliography.application.bibliography import Bibliography
from ebl.dictionary.application.dictionary import Dictionary
from ebl.files.application.file_repository import File, FileRepository
from ebl.fragmentarium.application.fragment_repository import FragmentRepository
from ebl.fragmentarium.domain.folios import Folio
from ebl.fragmentarium.domain.fragment import Fragment
from ebl.fragmentarium.domain.fragment_info import FragmentInfo
from ebl.fragmentarium.domain.museum_number import MuseumNumber
from ebl.transliteration.domain.transliteration_query import TransliterationQuery


class FragmentFinder:
    def __init__(
        self,
        bibliography: Bibliography,
        repository: FragmentRepository,
        dictionary: Dictionary,
        photos: FileRepository,
        folios: FileRepository,
    ):

        self._bibliography = bibliography
        self._repository = repository
        self._dictionary = dictionary
        self._photos = photos
        self._folios = folios

    def find(self, number: MuseumNumber) -> Tuple[Fragment, bool]:
        return (
            self._repository.query_by_museum_number(number),
            self._photos.query_if_file_exists(f"{number}.jpg"),
        )

    def search(self, number: str) -> List[FragmentInfo]:
        return list(
            map(
                FragmentInfo.of,
                self._repository.query_by_fragment_cdli_or_accession_number(number),
            )
        )

    def search_references_in_fragment_infos(
        self, id: str, pages: str
    ) -> List[FragmentInfo]:
        fragment_infos = self.search_references(id, pages)
        fragment_infos_with_documents = []
        for fragment_info in fragment_infos:
            references_with_documents = [
                reference.set_document(self._bibliography.find(reference.id))
                for reference in fragment_info.references
            ]
            fragment_infos_with_documents.append(
                fragment_info.set_references(references_with_documents)
            )
        return fragment_infos_with_documents

    def search_references(
        self, reference_id: str, reference_pages: str
    ) -> List[FragmentInfo]:
        return list(
            map(
                FragmentInfo.of,
                self._repository.query_by_id_and_page_in_references(
                    reference_id, reference_pages
                ),
            )
        )

    def search_transliteration(self, query: TransliterationQuery) -> List[FragmentInfo]:
        if query.is_empty():
            return []
        else:
            return [
                FragmentInfo.of(fragment, fragment.get_matching_lines(query))
                for fragment in self._repository.query_by_transliteration(query)
            ]

    def find_random(self) -> List[FragmentInfo]:
        return list(
            map(FragmentInfo.of, self._repository.query_random_by_transliterated())
        )

    def find_interesting(self) -> List[FragmentInfo]:
        return list(
            map(FragmentInfo.of, (self._repository.query_path_of_the_pioneers()))
        )

    def folio_pager(
        self, folio_name: str, folio_number: str, number: MuseumNumber
    ) -> dict:
        return self._repository.query_next_and_previous_folio(
            folio_name, folio_number, number
        )

    def fragment_pager(self, number: MuseumNumber) -> dict:
        return self._repository.query_next_and_previous_fragment(number)

    def find_folio(self, folio: Folio) -> File:
        file_name = folio.file_name
        return self._folios.query_by_file_name(file_name)

    def find_photo(self, number: str) -> File:
        file_name = f"{number}.jpg"
        return self._photos.query_by_file_name(file_name)
