from unittest.mock import Mock

import pytest
from pymongo.database import Database
from pymongo.errors import AutoReconnect
from pymongo.results import UpdateResult

from ebl.bibliography.application.bibliography import Bibliography
from ebl.bibliography.application.identity_management import (
    BibliographyIdentityManagement,
)
from ebl.bibliography.application.lookup_reservation import LookupReservationState
from ebl.bibliography.infrastructure.bibliography import MongoBibliographyRepository
from ebl.changelog import Changelog
from ebl.tests.bibliography.bibliography_test_helpers import IdentityFixtures
from ebl.tests.bibliography.identity_management_test_helpers import (
    alias,
    entry,
    reservation_state,
    stored,
)
from ebl.users.domain.user import User


@pytest.fixture
def identity_fixtures(
    bibliography: Bibliography,
    bibliography_repository: MongoBibliographyRepository,
    changelog: Changelog,
    user: User,
) -> IdentityFixtures:
    return IdentityFixtures(bibliography, bibliography_repository, changelog, user)


def test_ambiguous_identity_cas_confirms_the_persisted_identity(
    monkeypatch: pytest.MonkeyPatch,
    database: Database,
    identity_fixtures: IdentityFixtures,
) -> None:
    bibliography, bibliography_repository, changelog, user = identity_fixtures
    source = entry(bibliography, user, "Q30000170")
    raw_collection = database["bibliography"]
    mocked_collection = Mock(wraps=raw_collection)
    update_calls = {"count": 0}

    def ambiguous_update(
        query: dict[str, object], update: dict[str, object]
    ) -> UpdateResult:
        update_calls["count"] += 1
        result = raw_collection.update_one(query, update)
        if update_calls["count"] == 1:
            assert result.matched_count == 1
            raise AutoReconnect("identity update outcome unknown")
        return result

    mocked_collection.update_one.side_effect = ambiguous_update
    monkeypatch.setattr(
        bibliography_repository._collection,
        "_MongoCollection__get_collection",
        lambda: mocked_collection,
    )
    identity_management = BibliographyIdentityManagement(
        bibliography_repository, changelog
    )

    result = identity_management.manage_identity(
        source["id"], {"addAliases": [alias("ambiguous-cas-alias")]}, user
    )

    assert update_calls["count"] == 2
    assert result["aliases"] == [alias("ambiguous-cas-alias")]
    assert stored(database, source["id"])["aliases"] == [alias("ambiguous-cas-alias")]
    assert (
        reservation_state(database, "ambiguous-cas-alias")
        == LookupReservationState.COMMITTED.value
    )
