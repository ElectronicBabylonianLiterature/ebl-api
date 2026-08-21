"""`_validate_redirect` only checks the forward walk from the entry being
changed. Deprecating a node onto a chain that is itself within the depth
limit can still push an *existing* predecessor -- a tombstone that already
redirects to that node -- past the limit, invisibly to a check that never
looks backward. See identity_validation.py's `_validate_inbound_chains`.
"""

import falcon
import pytest

from ebl.tests.bibliography.identity_management_test_helpers import (
    admin_client,
    description,
    entry,
    manage_identity,
    stored,
)


@pytest.fixture
def client(context):
    return admin_client(context)


def deprecate(client, id_: str, target_id: str):
    return manage_identity(client, id_, {"deprecateTo": target_id})


def test_extending_a_chain_past_a_maximal_inbound_tombstone_is_rejected(
    client, database, bibliography, user
):
    # A pre-existing, already-valid 4-hop chain: B -> C -> D -> E -> F.
    b = entry(bibliography, user, "Q30000170")
    c = entry(bibliography, user, "Q30000171")
    d = entry(bibliography, user, "Q30000172")
    e = entry(bibliography, user, "Q30000173")
    f = entry(bibliography, user, "Q30000174")
    assert deprecate(client, e["id"], f["id"]).status == falcon.HTTP_OK
    assert deprecate(client, d["id"], e["id"]).status == falcon.HTTP_OK
    assert deprecate(client, c["id"], d["id"]).status == falcon.HTTP_OK
    assert deprecate(client, b["id"], c["id"]).status == falcon.HTTP_OK

    # One pre-existing inbound hop onto a still-live A: X -> A.
    a = entry(bibliography, user, "Q30000175")
    x = entry(bibliography, user, "Q30000176")
    assert deprecate(client, x["id"], a["id"]).status == falcon.HTTP_OK

    # A's own forward walk (A -> B -> C -> D -> E -> F) is exactly 5 hops and
    # would be accepted in isolation, but X's now needs 6.
    result = deprecate(client, a["id"], b["id"])

    assert result.status == falcon.HTTP_UNPROCESSABLE_ENTITY
    assert "maximum depth" in description(result)
    assert "deprecated" not in stored(database, a["id"])
    assert stored(database, x["id"])["redirectTo"] == a["id"]


def test_extending_a_chain_within_the_limit_still_succeeds(
    client, database, bibliography, user
):
    b = entry(bibliography, user, "Q30000180")
    c = entry(bibliography, user, "Q30000181")
    a = entry(bibliography, user, "Q30000182")
    x = entry(bibliography, user, "Q30000183")
    assert deprecate(client, b["id"], c["id"]).status == falcon.HTTP_OK
    assert deprecate(client, x["id"], a["id"]).status == falcon.HTTP_OK

    result = deprecate(client, a["id"], b["id"])

    assert result.status == falcon.HTTP_OK
    assert stored(database, a["id"])["deprecated"] is True
    assert bibliography.find(x["id"])["id"] == c["id"]


def test_a_predecessor_with_no_inbound_chain_of_its_own_is_unaffected(
    client, database, bibliography, user
):
    a = entry(bibliography, user, "Q30000184")
    b = entry(bibliography, user, "Q30000185")

    result = deprecate(client, a["id"], b["id"])

    assert result.status == falcon.HTTP_OK
    assert stored(database, a["id"])["deprecated"] is True
