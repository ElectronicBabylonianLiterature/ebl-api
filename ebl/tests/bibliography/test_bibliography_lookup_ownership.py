"""A redirect target must not be able to claim a value its own tombstone
still physically stores, even when that value predates the reservation
system and therefore has no reservation row of its own.
"""

from dataclasses import dataclass

import pytest

from ebl.bibliography.application.bibliography import Bibliography
from ebl.bibliography.application.bibliography_identity import (
    BibliographyIdentityContext,
    update_with_identity_claims,
)
from ebl.bibliography.application.bibliography_repository import LookupValueInUseError
from ebl.bibliography.infrastructure.bibliography import MongoBibliographyRepository
from ebl.changelog import Changelog
from ebl.tests.factories.bibliography import BibliographyEntryFactory
from ebl.users.domain.user import User

RESERVATIONS = "bibliography_lookup_reservations"
CHANGELOG = "changelog"


def bibliography_entry(id_: str, **overrides):
    return BibliographyEntryFactory.build(
        id=id_, DOI=f"10.1000/{id_}", PMID=id_, **overrides
    )


def alias(value: str):
    return {"value": value, "normalizedValue": value}


@dataclass(frozen=True)
class IdentityFixtures:
    bibliography: Bibliography
    repository: MongoBibliographyRepository
    changelog: Changelog
    user: User


@pytest.fixture
def identity_fixtures(
    bibliography, bibliography_repository, changelog, user
) -> IdentityFixtures:
    return IdentityFixtures(bibliography, bibliography_repository, changelog, user)


def apply_identity(fixtures: IdentityFixtures, entry_id: str, **changes):
    stored = fixtures.repository.query_by_id(entry_id)
    update_with_identity_claims(
        BibliographyIdentityContext(
            fixtures.repository, fixtures.changelog, fixtures.bibliography.find
        ),
        {**stored, **changes},
        fixtures.user,
        stored,
    )


def forget_reservation(database, value: str):
    """Simulate a legacy identity value that predates the reservation system."""
    database[RESERVATIONS].delete_one({"_id": value})


@pytest.fixture
def loser_and_winner(identity_fixtures, database):
    loser = bibliography_entry("Q30000001", citationKey="shared-key")
    winner = bibliography_entry("Q30000002")
    identity_fixtures.bibliography.create(loser, identity_fixtures.user)
    identity_fixtures.bibliography.create(winner, identity_fixtures.user)
    forget_reservation(database, "shared-key")
    apply_identity(
        identity_fixtures, loser["id"], deprecated=True, redirectTo=winner["id"]
    )
    return loser, winner


def test_deprecated_unreserved_citation_key_blocks_the_redirect_target(
    identity_fixtures, loser_and_winner
):
    _loser, winner = loser_and_winner

    with pytest.raises(LookupValueInUseError):
        apply_identity(identity_fixtures, winner["id"], citationKey="shared-key")


def test_deprecated_unreserved_alias_blocks_the_redirect_target(
    identity_fixtures, database
):
    loser = bibliography_entry("Q30000003", aliases=[alias("shared-alias")])
    winner = bibliography_entry("Q30000004")
    identity_fixtures.bibliography.create(loser, identity_fixtures.user)
    identity_fixtures.bibliography.create(winner, identity_fixtures.user)
    forget_reservation(database, "shared-alias")
    apply_identity(
        identity_fixtures, loser["id"], deprecated=True, redirectTo=winner["id"]
    )

    with pytest.raises(LookupValueInUseError):
        apply_identity(identity_fixtures, winner["id"], aliases=[alias("shared-alias")])


def test_normalized_alias_collision_remains_blocked(identity_fixtures, database):
    loser = bibliography_entry(
        "Q30000005",
        aliases=[{"value": "Shared Alias", "normalizedValue": "shared-alias"}],
    )
    winner = bibliography_entry("Q30000006")
    identity_fixtures.bibliography.create(loser, identity_fixtures.user)
    identity_fixtures.bibliography.create(winner, identity_fixtures.user)
    forget_reservation(database, "shared-alias")
    apply_identity(
        identity_fixtures, loser["id"], deprecated=True, redirectTo=winner["id"]
    )

    with pytest.raises(LookupValueInUseError):
        apply_identity(
            identity_fixtures,
            winner["id"],
            aliases=[{"value": "shared alias", "normalizedValue": "shared-alias"}],
        )


def test_rejected_claim_leaves_reservations_unchanged(
    identity_fixtures, database, loser_and_winner
):
    _loser, winner = loser_and_winner
    count_before = database[RESERVATIONS].count_documents({})

    with pytest.raises(LookupValueInUseError):
        apply_identity(identity_fixtures, winner["id"], citationKey="shared-key")

    assert database[RESERVATIONS].count_documents({}) == count_before
    assert database[RESERVATIONS].count_documents({"_id": "shared-key"}) == 0


def test_rejected_claim_leaves_bibliography_documents_unchanged(
    identity_fixtures, loser_and_winner
):
    loser, winner = loser_and_winner

    with pytest.raises(LookupValueInUseError):
        apply_identity(identity_fixtures, winner["id"], citationKey="shared-key")

    assert identity_fixtures.repository.query_by_id(loser["id"])["citationKey"] == (
        "shared-key"
    )
    assert "citationKey" not in identity_fixtures.repository.query_by_id(winner["id"])


def test_rejected_claim_leaves_the_changelog_unchanged(
    identity_fixtures, database, loser_and_winner
):
    _loser, winner = loser_and_winner
    count_before = database[CHANGELOG].count_documents({})

    with pytest.raises(LookupValueInUseError):
        apply_identity(identity_fixtures, winner["id"], citationKey="shared-key")

    assert database[CHANGELOG].count_documents({}) == count_before


def test_a_normal_read_through_the_value_still_follows_the_redirect(
    bibliography, loser_and_winner
):
    _loser, winner = loser_and_winner

    assert bibliography.find("shared-key")["id"] == winner["id"]


def test_an_unrelated_new_value_can_still_be_claimed(
    identity_fixtures, loser_and_winner
):
    _loser, winner = loser_and_winner

    apply_identity(identity_fixtures, winner["id"], citationKey="genuinely-free-key")

    assert (
        identity_fixtures.bibliography.find("genuinely-free-key")["id"]
        == (winner["id"])
    )
