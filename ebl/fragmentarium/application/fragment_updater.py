from typing import Tuple

from ebl.bibliography.application.bibliography import Bibliography
from ebl.bibliography.domain.reference import Reference
from ebl.changelog import Changelog
from ebl.files.application.file_repository import FileRepository
from ebl.fragmentarium.application.fragment_repository import \
    FragmentRepository
from ebl.fragmentarium.domain.fragment import Fragment, FragmentNumber
from ebl.fragmentarium.domain.transliteration_update import \
    TransliterationUpdate
from ebl.fragmentarium.infrastructure.fragment_schema import FragmentSchema
from ebl.transliteration.domain.lemmatization import Lemmatization
from ebl.users.domain.user import User

COLLECTION = 'fragments'


class FragmentUpdater:

    def __init__(self,
                 repository: FragmentRepository,
                 changelog,
                 bibliography):

        self._repository = repository
        self._changelog = changelog
        self._bibliography = bibliography

    def update_transliteration(self,
                               number: FragmentNumber,
                               transliteration: TransliterationUpdate,
                               user: User) -> Fragment:
        fragment = self._repository.query_by_fragment_number(number)

        updated_fragment = fragment.update_transliteration(
            transliteration,
            user
        )

        self._create_changlelog(user, fragment, updated_fragment)
        self._repository.update_transliteration(updated_fragment)

        return updated_fragment

    def update_lemmatization(self,
                             number: FragmentNumber,
                             lemmatization: Lemmatization,
                             user: User) -> Fragment:
        fragment = self._repository.query_by_fragment_number(number)
        updated_fragment = fragment.update_lemmatization(
            lemmatization
        )

        self._create_changlelog(user, fragment, updated_fragment)
        self._repository.update_lemmatization(updated_fragment)

        return updated_fragment

    def update_references(self,
                          number: FragmentNumber,
                          references: Tuple[Reference, ...],
                          user: User) -> Fragment:
        fragment = self._repository.query_by_fragment_number(number)
        self._bibliography.validate_references(references)

        updated_fragment = fragment.set_references(references)

        self._create_changlelog(user, fragment, updated_fragment)
        self._repository.update_references(updated_fragment)

        return updated_fragment

    def _create_changlelog(self,
                           user: User,
                           fragment: Fragment,
                           updated_fragment: Fragment) -> None:
        schema = FragmentSchema()
        self._changelog.create(
            COLLECTION,
            user.profile,
            schema.dump(fragment),
            schema.dump(updated_fragment)
        )
