from typing import Optional, Sequence

from ebl.bibliography.application.bibliography_repository import BibliographyRepository
from ebl.bibliography.application.serialization import create_mongo_entry
from ebl.bibliography.domain.reference import Reference
from ebl.changelog import Changelog
from ebl.errors import DataError, NotFoundError
from ebl.users.domain.user import User

COLLECTION = "bibliography"


class Bibliography:
    def __init__(self, repository: BibliographyRepository, changelog: Changelog):
        self._repository = repository
        self._changelog = changelog

    def create(self, entry, user: User) -> str:
        self._changelog.create(
            COLLECTION, user.profile, {"_id": entry["id"]}, create_mongo_entry(entry),
        )
        return self._repository.create(entry)

    def find(self, id_: str):
        return self._repository.query_by_id(id_)

    def update(self, entry, user: User):
        old_entry = self._repository.query_by_id(entry["id"])
        self._changelog.create(
            COLLECTION,
            user.profile,
            create_mongo_entry(old_entry),
            create_mongo_entry(entry),
        )
        self._repository.update(entry)

    def search(
        self,
        query
    ) -> list:
        first_result = self._repository.query_by_author_year_and_title(
            query[0], query[1], query[2]
        )
        second_result = self._repository.query_by_container_title_and_collection_number(
            query[0], query[1]
        )
        return first_result + [x for x in second_result if x not in first_result]

    def search_author_year_and_title(
        self,
        author: Optional[str] = None,
        year: Optional[int] = None,
        title: Optional[str] = None,
    ):
        return self._repository.query_by_author_year_and_title(author, year, title)

    def search_container_title_and_collection_number(
        self,
        container_title: Optional[str] = None,
        collection_number: Optional[str] = None,
    ):
        return self._repository.query_by_container_title_and_collection_number(
            container_title, collection_number)

    def validate_references(self, references: Sequence[Reference]):
        def is_invalid(reference):
            try:
                self.find(reference.id)
                return False
            except NotFoundError:
                return True

        invalid_references = [
            reference.id for reference in references if is_invalid(reference)
        ]
        if invalid_references:
            raise DataError(
                "Unknown bibliography entries: " f'{", ".join(invalid_references)}.'
            )
