from typing import Any, Callable, Literal, NamedTuple, Protocol

from ebl.bibliography.application.bibliography import Bibliography
from ebl.bibliography.application.bibliography_repository import (
    BibliographyRepository,
)
from ebl.bibliography.infrastructure.bibliography import MongoBibliographyRepository
from ebl.changelog import Changelog
from ebl.tests.factories.bibliography import BibliographyEntryFactory
from ebl.users.domain.user import User


class MongoEntryFactory(Protocol):
    def __call__(
        self, bibliography_entry: dict[str, Any] | None = None
    ) -> dict[str, Any]: ...


class BibliographyFixtures(NamedTuple):
    bibliography: Bibliography
    repository: BibliographyRepository
    user: User
    changelog: Changelog
    create_mongo_entry: MongoEntryFactory


class IdentityFixtures(NamedTuple):
    bibliography: Bibliography
    repository: MongoBibliographyRepository
    changelog: Changelog
    user: User


def assert_two_part_search(
    fixtures: BibliographyFixtures,
    when: Callable[[object], Any],
    first_field: str,
    second_field: str,
    query_kind: Literal["container", "title"],
) -> None:
    entry = BibliographyEntryFactory.build()
    first = entry[first_field]
    second = entry[second_field]
    query = f"{first} {second}"
    when(fixtures.repository).query_by_author_year_and_title(
        first, int(second), None
    ).thenReturn([])
    if query_kind == "container":
        when(fixtures.repository).query_by_container_title_and_collection_number(
            first, second
        ).thenReturn([entry])
    else:
        when(fixtures.repository).query_by_title_short_and_volume(
            first, second
        ).thenReturn([entry])
    assert fixtures.bibliography.search(query) == [entry]
