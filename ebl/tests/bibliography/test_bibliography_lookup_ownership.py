"""A redirect target must not be able to claim a value its own tombstone
still physically stores, even when that value predates the reservation
system and therefore has no reservation row of its own.
"""

import pytest

from ebl.bibliography.application.bibliography_identity import (
    BibliographyIdentityContext,
    update_with_identity_claims,
)
from ebl.bibliography.application.bibliography_repository import LookupValueInUseError
from ebl.tests.factories.bibliography import BibliographyEntryFactory

RESERVATIONS = "bibliography_lookup_reservations"
CHANGELOG = "changelog"


def bibliography_entry(id_: str, **overrides):
    return BibliographyEntryFactory.build(
        id=id_, DOI=f"10.1000/{id_}", PMID=id_, **overrides
    )


def alias(value: str):
    return {"value": value, "normalizedValue": value}


def apply_identity(bibliography, repository, changelog, user, entry_id, **changes):
    stored = repository.query_by_id(entry_id)
    update_with_identity_claims(
        BibliographyIdentityContext(repository, changelog, bibliography.find),
        {**stored, **changes},
        user,
        stored,
    )


def forget_reservation(database, value: str):
    """Simulate a legacy identity value that predates the reservation system."""
    database[RESERVATIONS].delete_one({"_id": value})


@pytest.fixture
def loser_and_winner(bibliography, bibliography_repository, changelog, user, database):
    loser = bibliography_entry("Q30000001", citationKey="shared-key")
    winner = bibliography_entry("Q30000002")
    bibliography.create(loser, user)
    bibliography.create(winner, user)
    forget_reservation(database, "shared-key")
    apply_identity(
        bibliography,
        bibliography_repository,
        changelog,
        user,
        loser["id"],
        deprecated=True,
        redirectTo=winner["id"],
    )
    return loser, winner


def test_deprecated_unreserved_citation_key_blocks_the_redirect_target(
    bibliography, bibliography_repository, changelog, user, loser_and_winner
):
    _loser, winner = loser_and_winner

    with pytest.raises(LookupValueInUseError):
        apply_identity(
            bibliography,
            bibliography_repository,
            changelog,
            user,
            winner["id"],
            citationKey="shared-key",
        )


def test_deprecated_unreserved_alias_blocks_the_redirect_target(
    bibliography, bibliography_repository, changelog, user, database
):
    loser = bibliography_entry("Q30000003", aliases=[alias("shared-alias")])
    winner = bibliography_entry("Q30000004")
    bibliography.create(loser, user)
    bibliography.create(winner, user)
    forget_reservation(database, "shared-alias")
    apply_identity(
        bibliography,
        bibliography_repository,
        changelog,
        user,
        loser["id"],
        deprecated=True,
        redirectTo=winner["id"],
    )

    with pytest.raises(LookupValueInUseError):
        apply_identity(
            bibliography,
            bibliography_repository,
            changelog,
            user,
            winner["id"],
            aliases=[alias("shared-alias")],
        )


def test_normalized_alias_collision_remains_blocked(
    bibliography, bibliography_repository, changelog, user, database
):
    loser = bibliography_entry(
        "Q30000005",
        aliases=[{"value": "Shared Alias", "normalizedValue": "shared-alias"}],
    )
    winner = bibliography_entry("Q30000006")
    bibliography.create(loser, user)
    bibliography.create(winner, user)
    forget_reservation(database, "shared-alias")
    apply_identity(
        bibliography,
        bibliography_repository,
        changelog,
        user,
        loser["id"],
        deprecated=True,
        redirectTo=winner["id"],
    )

    with pytest.raises(LookupValueInUseError):
        apply_identity(
            bibliography,
            bibliography_repository,
            changelog,
            user,
            winner["id"],
            aliases=[{"value": "shared alias", "normalizedValue": "shared-alias"}],
        )


def test_rejected_claim_leaves_reservations_unchanged(
    bibliography, bibliography_repository, changelog, user, database, loser_and_winner
):
    _loser, winner = loser_and_winner
    count_before = database[RESERVATIONS].count_documents({})

    with pytest.raises(LookupValueInUseError):
        apply_identity(
            bibliography,
            bibliography_repository,
            changelog,
            user,
            winner["id"],
            citationKey="shared-key",
        )

    assert database[RESERVATIONS].count_documents({}) == count_before
    assert database[RESERVATIONS].count_documents({"_id": "shared-key"}) == 0


def test_rejected_claim_leaves_bibliography_documents_unchanged(
    bibliography, bibliography_repository, changelog, user, loser_and_winner
):
    loser, winner = loser_and_winner

    with pytest.raises(LookupValueInUseError):
        apply_identity(
            bibliography,
            bibliography_repository,
            changelog,
            user,
            winner["id"],
            citationKey="shared-key",
        )

    assert bibliography_repository.query_by_id(loser["id"])["citationKey"] == (
        "shared-key"
    )
    assert "citationKey" not in bibliography_repository.query_by_id(winner["id"])


def test_rejected_claim_leaves_the_changelog_unchanged(
    bibliography, bibliography_repository, changelog, user, database, loser_and_winner
):
    _loser, winner = loser_and_winner
    count_before = database[CHANGELOG].count_documents({})

    with pytest.raises(LookupValueInUseError):
        apply_identity(
            bibliography,
            bibliography_repository,
            changelog,
            user,
            winner["id"],
            citationKey="shared-key",
        )

    assert database[CHANGELOG].count_documents({}) == count_before


def test_a_normal_read_through_the_value_still_follows_the_redirect(
    bibliography, loser_and_winner
):
    _loser, winner = loser_and_winner

    assert bibliography.find("shared-key")["id"] == winner["id"]


def test_an_unrelated_new_value_can_still_be_claimed(
    bibliography, bibliography_repository, changelog, user, loser_and_winner
):
    _loser, winner = loser_and_winner

    apply_identity(
        bibliography,
        bibliography_repository,
        changelog,
        user,
        winner["id"],
        citationKey="genuinely-free-key",
    )

    assert bibliography.find("genuinely-free-key")["id"] == winner["id"]
