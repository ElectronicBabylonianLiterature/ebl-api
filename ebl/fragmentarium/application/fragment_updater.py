from typing import Sequence, Tuple

from ebl.bibliography.application.bibliography import Bibliography
from ebl.bibliography.domain.reference import Reference
from ebl.changelog import Changelog
from ebl.files.application.file_repository import FileRepository
from ebl.fragmentarium.application.fragment_repository import FragmentRepository
from ebl.fragmentarium.application.fragment_schema import FragmentSchema
from ebl.fragmentarium.domain.fragment import Fragment, Genre
from ebl.transliteration.application.parallel_line_injector import ParallelLineInjector
from ebl.transliteration.domain.markup import MarkupPart
from ebl.transliteration.domain.museum_number import MuseumNumber
from ebl.fragmentarium.domain.transliteration_update import TransliterationUpdate
from ebl.lemmatization.domain.lemmatization import Lemmatization
from ebl.users.domain.user import User

COLLECTION = "fragments"


class FragmentUpdater:
    def __init__(
        self,
        repository: FragmentRepository,
        changelog: Changelog,
        bibliography: Bibliography,
        photos: FileRepository,
        parallel_injector: ParallelLineInjector,
    ):

        self._repository = repository
        self._changelog = changelog
        self._bibliography = bibliography
        self._photos = photos
        self._parallel_injector = parallel_injector

    def update_transliteration(
        self,
        number: MuseumNumber,
        transliteration: TransliterationUpdate,
        user: User,
        ignore_lowest_join: bool = False,
    ) -> Tuple[Fragment, bool]:
        fragment = self._repository.query_by_museum_number(number)

        updated_fragment = (
            fragment.update_transliteration(transliteration, user)
            if ignore_lowest_join
            else fragment.update_lowest_join_transliteration(transliteration, user)
        )
        self._create_changlelog(user, fragment, updated_fragment)
        self._repository.update_transliteration(updated_fragment)

        return self._create_result(updated_fragment)

    def update_introduction(
        self, number: MuseumNumber, introduction: Sequence[MarkupPart], user: User
    ) -> Tuple[Fragment, bool]:
        fragment = self._repository.query_by_museum_number(number)
        updated_fragment = fragment.set_introduction(introduction)

        self._create_changlelog(user, fragment, updated_fragment)
        self._repository.update_introduction(updated_fragment)

        return self._create_result(updated_fragment)

    def update_genres(
        self, number: MuseumNumber, genres: Sequence[Genre], user: User
    ) -> Tuple[Fragment, bool]:
        fragment = self._repository.query_by_museum_number(number)
        updated_fragment = fragment.set_genres(genres)

        self._create_changlelog(user, fragment, updated_fragment)
        self._repository.update_genres(updated_fragment)

        return self._create_result(updated_fragment)

    def update_lemmatization(
        self, number: MuseumNumber, lemmatization: Lemmatization, user: User
    ) -> Tuple[Fragment, bool]:
        fragment = self._repository.query_by_museum_number(number)
        updated_fragment = fragment.update_lemmatization(lemmatization)

        self._create_changlelog(user, fragment, updated_fragment)
        self._repository.update_lemmatization(updated_fragment)

        return self._create_result(updated_fragment)

    def update_references(
        self, number: MuseumNumber, references: Sequence[Reference], user: User
    ) -> Tuple[Fragment, bool]:
        fragment = self._repository.query_by_museum_number(number)
        self._bibliography.validate_references(references)

        updated_fragment = fragment.set_references(references)

        self._create_changlelog(user, fragment, updated_fragment)
        self._repository.update_references(updated_fragment)

        return self._create_result(self._repository.query_by_museum_number(number))

    def _create_result(self, fragment: Fragment) -> Tuple[Fragment, bool]:
        return (
            fragment.set_text(
                self._parallel_injector.inject_transliteration(fragment.text)
            ),
            self._photos.query_if_file_exists(f"{fragment.number}.jpg"),
        )

    def _create_changlelog(
        self, user: User, fragment: Fragment, updated_fragment: Fragment
    ) -> None:
        schema = FragmentSchema()
        fragment_id = str(fragment.number)
        self._changelog.create(
            COLLECTION,
            user.profile,
            {"_id": fragment_id, **schema.dump(fragment)},
            {"_id": fragment_id, **schema.dump(updated_fragment)},
        )
