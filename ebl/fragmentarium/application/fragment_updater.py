from enum import Enum
from typing import List, Sequence, Tuple, Optional

from ebl.bibliography.application.bibliography import Bibliography
from ebl.bibliography.domain.reference import Reference
from ebl.changelog import Changelog
from ebl.files.application.file_repository import FileRepository
from ebl.fragmentarium.application.fragment_repository import FragmentRepository
from ebl.fragmentarium.application.fragment_schema import FragmentSchema
from ebl.fragmentarium.domain.archaeology import Archaeology
from ebl.fragmentarium.domain.fragment import Fragment, Genre, Script
from ebl.fragmentarium.domain.named_entity import EntityAnnotationSpan
from ebl.fragmentarium.domain.token_annotation import TextLemmaAnnotation
from ebl.transliteration.application.parallel_line_injector import ParallelLineInjector
from ebl.transliteration.domain.museum_number import MuseumNumber
from ebl.fragmentarium.domain.transliteration_update import TransliterationUpdate
from ebl.lemmatization.domain.lemmatization import Lemmatization
from ebl.users.domain.user import User
from ebl.fragmentarium.domain.date import Date
from ebl.fragmentarium.domain.colophon import Colophon

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

    def update_edition(
        self,
        number: MuseumNumber,
        user: User,
        introduction: Optional[str] = None,
        notes: Optional[str] = None,
        transliteration: Optional[TransliterationUpdate] = None,
        ignore_lowest_join: bool = False,
    ) -> Tuple[Fragment, bool]:
        original_fragment = fragment = self._repository.query_by_museum_number(number)

        if introduction is not None:
            fragment = fragment.set_introduction(introduction)
            self._repository.update_field("introduction", fragment)

        if notes is not None:
            fragment = fragment.set_notes(notes)
            self._repository.update_field("notes", fragment)

        if transliteration is not None:
            fragment = (
                fragment.update_transliteration(transliteration, user)
                if ignore_lowest_join
                else fragment.update_lowest_join_transliteration(transliteration, user)
            )
            self._repository.update_field("transliteration", fragment)

        self._create_changelog(user, original_fragment, fragment)

        return self._create_result(fragment)

    def update_script(
        self, number: MuseumNumber, script: Script, user: User
    ) -> Tuple[Fragment, bool]:
        fragment = self._repository.query_by_museum_number(number)
        updated_fragment = fragment.set_script(script)

        self._create_changelog(user, fragment, updated_fragment)
        self._repository.update_field("script", updated_fragment)

        return self._create_result(updated_fragment)

    def update_date(
        self, number: MuseumNumber, date: Optional[Date], user: User
    ) -> Tuple[Fragment, bool]:
        fragment = self._repository.query_by_museum_number(number)
        updated_fragment = fragment.set_date(date)
        self._create_changelog(user, fragment, updated_fragment)
        self._repository.update_field("date", updated_fragment)

        return self._create_result(updated_fragment)

    def update_dates_in_text(
        self, number: MuseumNumber, dates_in_text: Sequence[Date], user: User
    ) -> Tuple[Fragment, bool]:
        fragment = self._repository.query_by_museum_number(number)
        updated_fragment = fragment.set_dates_in_text(dates_in_text)
        self._create_changelog(user, fragment, updated_fragment)
        self._repository.update_field("dates_in_text", updated_fragment)

        return self._create_result(updated_fragment)

    def update_genres(
        self, number: MuseumNumber, genres: Sequence[Genre], user: User
    ) -> Tuple[Fragment, bool]:
        fragment = self._repository.query_by_museum_number(number)
        updated_fragment = fragment.set_genres(genres)

        self._create_changelog(user, fragment, updated_fragment)
        self._repository.update_field("genres", updated_fragment)

        return self._create_result(updated_fragment)

    def update_scopes(
        self, number: MuseumNumber, scopes: Sequence[Enum]
    ) -> Tuple[Fragment, bool]:
        fragment = self._repository.query_by_museum_number(number)
        updated_fragment = fragment.set_scopes(scopes)
        self._repository.update_field("authorized_scopes", updated_fragment)
        return self._create_result(updated_fragment)

    def update_lemmatization(
        self, number: MuseumNumber, lemmatization: Lemmatization, user: User
    ) -> Tuple[Fragment, bool]:
        fragment = self._repository.query_by_museum_number(number)
        updated_fragment = fragment.update_lemmatization(lemmatization)

        self._create_changelog(user, fragment, updated_fragment)
        self._repository.update_field("lemmatization", updated_fragment)

        return self._create_result(updated_fragment)

    def update_lemma_annotation(
        self, number: MuseumNumber, annotation: TextLemmaAnnotation, user: User
    ) -> Tuple[Fragment, bool]:
        fragment = self._repository.query_by_museum_number(number)
        updated_fragment = fragment.update_lemma_annotation(annotation)

        self._create_changelog(user, fragment, updated_fragment)
        self._repository.update_field("lemmatization", updated_fragment)

        return self._create_result(updated_fragment)

    def update_references(
        self, number: MuseumNumber, references: Sequence[Reference], user: User
    ) -> Tuple[Fragment, bool]:
        fragment = self._repository.query_by_museum_number(number)
        self._bibliography.validate_references(references)

        updated_fragment = fragment.set_references(references)

        self._create_changelog(user, fragment, updated_fragment)
        self._repository.update_field("references", updated_fragment)

        return self._create_result(self._repository.query_by_museum_number(number))

    def update_archaeology(
        self, number: MuseumNumber, archaeology: Archaeology, user: User
    ) -> Tuple[Fragment, bool]:
        fragment = self._repository.query_by_museum_number(number)
        updated_fragment = fragment.set_archaeology(archaeology)

        self._repository.update_field("archaeology", updated_fragment)

        return self._create_result(updated_fragment)

    def update_colophon(
        self, number: MuseumNumber, colophon: Colophon, user: User
    ) -> Tuple[Fragment, bool]:
        fragment = self._repository.query_by_museum_number(number)
        updated_fragment = fragment.set_colophon(colophon)

        self._repository.update_field("colophon", updated_fragment)

        return self._create_result(updated_fragment)

    def update_ocred_signs(
        self, number: MuseumNumber, ocred_signs: str, user: User
    ) -> Tuple[Fragment, bool]:
        fragment = self._repository.query_by_museum_number(number)
        updated_fragment = fragment.set_ocred_signs(ocred_signs)

        self._create_changelog(user, fragment, updated_fragment)
        self._repository.update_field("ocredSigns", updated_fragment)

        return self._create_result(updated_fragment)

    def _create_result(self, fragment: Fragment) -> Tuple[Fragment, bool]:
        return (
            fragment.set_text(
                self._parallel_injector.inject_transliteration(fragment.text)
            ),
            self._photos.query_if_file_exists(f"{fragment.number}.jpg"),
        )

    def _create_changelog(
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

    def update_named_entities(
        self, number: MuseumNumber, annotations: List[EntityAnnotationSpan], user: User
    ) -> Tuple[Fragment, bool]:
        fragment = self._repository.query_by_museum_number(number)
        updated_fragment = fragment.set_named_entities(annotations)

        self._create_changelog(user, fragment, updated_fragment)
        self._repository.update_field("named_entities", updated_fragment)

        return self._create_result(updated_fragment)
