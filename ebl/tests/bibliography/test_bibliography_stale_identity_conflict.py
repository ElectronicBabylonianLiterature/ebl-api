"""Cross-request conflict contract for the generic metadata update.

A client can only submit server-owned state it fetched earlier, so when that
state disagrees with what is stored the server cannot tell a stale editor from
a client inventing an identity value. Both answer `409 Conflict` and neither
persists the submitted value, which keeps the remedy the same as for a write
that races the request: reload the entry and retry.
"""

from dataclasses import dataclass
from typing import Callable

import falcon
import pytest
from falcon import testing
from pymongo.database import Database

from ebl.bibliography.application.bibliography import Bibliography
from ebl.bibliography.application.bibliography_identity import (
    BibliographyIdentityContext,
    update_with_identity_claims,
)
from ebl.users.domain.user import User
from ebl.tests.bibliography.identity_preservation_test_helpers import (
    CITATION_KEY,
    CORRECTED_TITLE,
    PARTNER_ALIAS,
    metadata_only_payload,
    post_entry,
    reservations,
)
from ebl.tests.factories.bibliography import BibliographyEntryFactory

CANONICAL_ID = "rla_9_388"
NEW_CITATION_KEY = "dossin1967Lb"
MERGED_ALIAS = {
    "value": "RN9001",
    "normalizedValue": "rn9001",
    "type": "legacy_id",
    "source": "duplicate_merge_2026-08-04",
    "status": "redirect",
}
ADDED_ALIASES = [PARTNER_ALIAS, MERGED_ALIAS]


@pytest.fixture
def identity_operation(bibliography, bibliography_repository, changelog, user):
    """Mutate identity the way a trusted operation would, bypassing the route."""

    def operate(entry: dict) -> None:
        update_with_identity_claims(
            BibliographyIdentityContext(
                bibliography_repository, changelog, bibliography.find
            ),
            entry,
            user,
        )

    return operate


@pytest.fixture
def fetched_entry(client, aliased_entry) -> dict:
    return client.simulate_get(f"/bibliography/{aliased_entry['id']}").json


def stale_payload(fetched_entry: dict) -> dict:
    return {**fetched_entry, "title": CORRECTED_TITLE}


def changelog_count(database, id_: str) -> int:
    return database["changelog"].count_documents({"resource_id": id_})


def test_stale_aliases_are_a_conflict(client, fetched_entry, identity_operation):
    identity_operation({**fetched_entry, "aliases": ADDED_ALIASES})

    result = post_entry(client, stale_payload(fetched_entry))

    assert result.status == falcon.HTTP_CONFLICT
    assert "aliases" in result.text
    assert "reload" in result.text


def test_stale_aliases_conflict_keeps_the_added_alias(
    client, bibliography, aliased_entry, fetched_entry, identity_operation
):
    identity_operation({**fetched_entry, "aliases": ADDED_ALIASES})

    post_entry(client, stale_payload(fetched_entry))
    stored_entry = bibliography.find(aliased_entry["id"])

    assert stored_entry["aliases"] == ADDED_ALIASES
    assert stored_entry["title"] == aliased_entry["title"]


def test_stale_citation_key_is_a_conflict(client, fetched_entry, identity_operation):
    identity_operation({**fetched_entry, "citationKey": NEW_CITATION_KEY})

    result = post_entry(client, stale_payload(fetched_entry))

    assert result.status == falcon.HTTP_CONFLICT
    assert "citationKey" in result.text


def test_stale_citation_key_conflict_keeps_the_new_key(
    client, bibliography, aliased_entry, fetched_entry, identity_operation
):
    identity_operation({**fetched_entry, "citationKey": NEW_CITATION_KEY})

    post_entry(client, stale_payload(fetched_entry))
    stored_entry = bibliography.find(aliased_entry["id"])

    assert stored_entry["citationKey"] == NEW_CITATION_KEY
    assert stored_entry["title"] == aliased_entry["title"]
    assert bibliography.find(NEW_CITATION_KEY)["id"] == aliased_entry["id"]


def test_stale_conflict_writes_no_changelog_entry(
    client, database, aliased_entry, fetched_entry, identity_operation
):
    identity_operation({**fetched_entry, "aliases": ADDED_ALIASES})
    before = changelog_count(database, aliased_entry["id"])

    post_entry(client, stale_payload(fetched_entry))

    assert changelog_count(database, aliased_entry["id"]) == before


def test_stale_conflict_claims_no_reservations(
    client, database, fetched_entry, identity_operation
):
    identity_operation({**fetched_entry, "citationKey": NEW_CITATION_KEY})
    before = reservations(database)

    post_entry(client, stale_payload(fetched_entry))

    assert reservations(database) == before


def test_reload_and_retry_after_a_stale_conflict_succeeds(
    client, bibliography, aliased_entry, fetched_entry, identity_operation
):
    identity_operation({**fetched_entry, "aliases": ADDED_ALIASES})
    conflict = post_entry(client, stale_payload(fetched_entry))

    reloaded_entry = client.simulate_get(f"/bibliography/{aliased_entry['id']}").json
    result = post_entry(client, stale_payload(reloaded_entry))
    stored_entry = bibliography.find(aliased_entry["id"])

    assert conflict.status == falcon.HTTP_CONFLICT
    assert result.status == falcon.HTTP_NO_CONTENT
    assert stored_entry["title"] == CORRECTED_TITLE
    assert stored_entry["aliases"] == ADDED_ALIASES
    assert stored_entry["citationKey"] == CITATION_KEY


def test_metadata_only_update_succeeds_after_an_identity_change(
    client, bibliography, aliased_entry, fetched_entry, identity_operation
):
    identity_operation({**fetched_entry, "aliases": ADDED_ALIASES})

    result = post_entry(client, metadata_only_payload(aliased_entry))
    stored_entry = bibliography.find(aliased_entry["id"])

    assert result.status == falcon.HTTP_NO_CONTENT
    assert stored_entry["title"] == CORRECTED_TITLE
    assert stored_entry["aliases"] == ADDED_ALIASES


def test_an_invented_identity_value_is_also_a_conflict(
    client, bibliography, aliased_entry, fetched_entry
):
    payload = {**stale_payload(fetched_entry), "citationKey": "invented1999Key"}

    result = post_entry(client, payload)
    stored_entry = bibliography.find(aliased_entry["id"])

    assert result.status == falcon.HTTP_CONFLICT
    assert stored_entry["citationKey"] == CITATION_KEY
    assert stored_entry["title"] == aliased_entry["title"]


@dataclass(frozen=True)
class StaleTombstoneResurrectionContext:
    client: testing.TestClient
    bibliography: Bibliography
    database: Database
    user: User
    aliased_entry: dict
    fetched_entry: dict
    identity_operation: Callable[[dict], None]


@pytest.fixture
def stale_tombstone_resurrection_context(
    request: pytest.FixtureRequest,
) -> StaleTombstoneResurrectionContext:
    return StaleTombstoneResurrectionContext(
        request.getfixturevalue("client"),
        request.getfixturevalue("bibliography"),
        request.getfixturevalue("database"),
        request.getfixturevalue("user"),
        request.getfixturevalue("aliased_entry"),
        request.getfixturevalue("fetched_entry"),
        request.getfixturevalue("identity_operation"),
    )


def test_a_stale_body_cannot_resurrect_a_tombstoned_entry(
    stale_tombstone_resurrection_context: StaleTombstoneResurrectionContext,
) -> None:
    context = stale_tombstone_resurrection_context
    context.bibliography.create(
        BibliographyEntryFactory.build(id=CANONICAL_ID, title="Canonical"),
        context.user,
    )
    context.identity_operation(
        {**context.fetched_entry, "deprecated": True, "redirectTo": CANONICAL_ID}
    )

    result = post_entry(context.client, stale_payload(context.fetched_entry))
    stored_entry = context.database["bibliography"].find_one(
        {"_id": context.aliased_entry["id"]}
    )

    assert result.status == falcon.HTTP_UNPROCESSABLE_ENTITY
    assert "is deprecated" in result.text
    assert stored_entry["deprecated"] is True
    assert stored_entry["redirectTo"] == CANONICAL_ID
    assert stored_entry["title"] == context.aliased_entry["title"]
    assert (
        context.bibliography.find(context.aliased_entry["id"])["id"] == CANONICAL_ID
    )


@pytest.mark.parametrize(
    "field,value",
    [("aliases", "not-a-list"), ("citationKey", 7), ("deprecated", "yes")],
)
def test_a_malformed_server_owned_value_is_rejected_by_the_schema(
    field, value, client, fetched_entry
):
    result = post_entry(client, {**stale_payload(fetched_entry), field: value})

    assert result.status == falcon.HTTP_BAD_REQUEST
