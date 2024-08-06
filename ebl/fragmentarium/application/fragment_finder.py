from enum import Enum
from typing import List, Optional, Sequence, Tuple

from ebl.bibliography.application.bibliography import Bibliography
from ebl.common.domain.scopes import Scope
from ebl.dictionary.application.dictionary_service import Dictionary
from ebl.files.application.file_repository import File, FileRepository
from ebl.fragmentarium.application.fragment_repository import FragmentRepository
from ebl.fragmentarium.domain.folios import Folio
from ebl.fragmentarium.domain.fragment import Fragment
from ebl.fragmentarium.domain.fragment_info import FragmentInfo
from ebl.fragmentarium.domain.fragment_pager_info import FragmentPagerInfo
from ebl.transliteration.application.parallel_line_injector import ParallelLineInjector
from ebl.transliteration.domain.museum_number import MuseumNumber


class ThumbnailSize(Enum):
    SMALL = 240
    MEDIUM = 480
    LARGE = 720

    @classmethod
    def from_string(cls, value: str):
        try:
            return cls[value.upper()]
        except KeyError as e:
            raise ValueError(f"Unknown thumbnail size: {value}") from e


class FragmentFinder:
    def __init__(
        self,
        bibliography: Bibliography,
        repository: FragmentRepository,
        dictionary: Dictionary,
        photos: FileRepository,
        folios: FileRepository,
        thumbnails: FileRepository,
        parallel_injector: ParallelLineInjector,
    ):
        self._bibliography = bibliography
        self._repository = repository
        self._dictionary = dictionary
        self._photos = photos
        self._folios = folios
        self._thumbnails = thumbnails
        self._parallel_injector = parallel_injector

    def find(
        self,
        number: MuseumNumber,
        lines: Optional[Sequence[int]] = None,
        exclude_lines=False,
    ) -> Tuple[Fragment, bool]:
        fragment = self._repository.query_by_museum_number(number, lines, exclude_lines)
        return (
            fragment.set_text(
                self._parallel_injector.inject_transliteration(fragment.text)
            ),
            self._photos.query_if_file_exists(f"{number}.jpg"),
        )

    def fetch_scopes(self, number: MuseumNumber) -> List[Scope]:
        return self._repository.fetch_scopes(number)

    def find_random(self, user_scopes: Sequence[Scope] = ()) -> List[FragmentInfo]:
        return list(
            map(
                FragmentInfo.of,
                self._repository.query_random_by_transliterated(user_scopes),
            )
        )

    def find_interesting(self, user_scopes: Sequence[Scope] = ()) -> List[FragmentInfo]:
        return list(
            map(
                FragmentInfo.of,
                (self._repository.query_path_of_the_pioneers(user_scopes)),
            )
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

    def find_thumbnail(self, number: str, width: ThumbnailSize) -> File:
        file_name = f"{number}_{width.value}.jpg"
        return self._thumbnails.query_by_file_name(file_name)
