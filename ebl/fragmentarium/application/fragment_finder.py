from typing import List, Optional, Sequence, Tuple

from ebl.bibliography.application.bibliography import Bibliography
from ebl.dictionary.application.dictionary_service import Dictionary
from ebl.files.application.file_repository import File, FileRepository
from ebl.fragmentarium.application.fragment_repository import FragmentRepository
from ebl.fragmentarium.domain.folios import Folio
from ebl.fragmentarium.domain.fragment import Fragment
from ebl.fragmentarium.domain.fragment_info import FragmentInfo
from ebl.fragmentarium.domain.fragment_pager_info import FragmentPagerInfo
from ebl.transliteration.application.parallel_line_injector import ParallelLineInjector
from ebl.transliteration.domain.museum_number import MuseumNumber


class FragmentFinder:
    def __init__(
        self,
        bibliography: Bibliography,
        repository: FragmentRepository,
        dictionary: Dictionary,
        photos: FileRepository,
        folios: FileRepository,
        parallel_injector: ParallelLineInjector,
    ):

        self._bibliography = bibliography
        self._repository = repository
        self._dictionary = dictionary
        self._photos = photos
        self._folios = folios
        self._parallel_injector = parallel_injector

    def find(
        self, number: MuseumNumber, lines: Optional[Sequence[int]] = None
    ) -> Tuple[Fragment, bool]:
        fragment = self._repository.query_by_museum_number(number, lines)
        return (
            fragment.set_text(
                self._parallel_injector.inject_transliteration(fragment.text)
            ),
            self._photos.query_if_file_exists(f"{number}.jpg"),
        )

    def fetch_scopes(self, number: MuseumNumber) -> List[str]:
        return self._repository.fetch_scopes(number)

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

    def fragment_pager(self, number: MuseumNumber) -> FragmentPagerInfo:
        return self._repository.query_next_and_previous_fragment(number)

    def find_folio(self, folio: Folio) -> File:
        file_name = folio.file_name
        return self._folios.query_by_file_name(file_name)

    def find_photo(self, number: str) -> File:
        file_name = f"{number}.jpg"
        return self._photos.query_by_file_name(file_name)
