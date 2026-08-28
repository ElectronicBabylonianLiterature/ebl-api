import falcon
import pytest

from ebl.bibliography.application.redirect_resolution import MAX_REDIRECT_DEPTH
from ebl.tests.bibliography.identity_management_test_helpers import (
    admin_client,
    body,
    description,
    entry,
    manage_identity,
    stored,
)


@pytest.fixture
def client(context):
    return admin_client(context)


def chain(bibliography, user, ids):
    for index, id_ in enumerate(ids):
        is_last = index == len(ids) - 1
        entry(
            bibliography,
            user,
            id_,
            **({} if is_last else {"deprecated": True, "redirectTo": ids[index + 1]}),
        )


def test_deprecate_to_a_valid_canonical_target(client, database, bibliography, user):
    entry(bibliography, user, "Q30000040")
    entry(bibliography, user, "Q30000041")

    result = manage_identity(client, "Q30000040", {"deprecateTo": "Q30000041"})

    assert result.status == falcon.HTTP_OK
    assert body(result)["deprecated"] is True
    assert body(result)["redirectTo"] == "Q30000041"
    assert stored(database, "Q30000040")["deprecated"] is True
    assert bibliography.find("Q30000040")["id"] == "Q30000041"


def test_self_redirect_is_rejected(client, database, bibliography, user):
    entry(bibliography, user, "Q30000042")

    result = manage_identity(client, "Q30000042", {"deprecateTo": "Q30000042"})

    assert result.status == falcon.HTTP_UNPROCESSABLE_ENTITY
    assert "cannot redirect to itself" in description(result)
    assert "deprecated" not in stored(database, "Q30000042")


def test_missing_target_is_rejected(client, database, bibliography, user):
    entry(bibliography, user, "Q30000043")

    result = manage_identity(client, "Q30000043", {"deprecateTo": "Q39999999"})

    assert result.status == falcon.HTTP_UNPROCESSABLE_ENTITY
    assert "Q39999999 not found" in description(result)
    assert "deprecated" not in stored(database, "Q30000043")


def test_two_record_cycle_is_rejected(client, database, bibliography, user):
    entry(bibliography, user, "Q30000044")
    entry(bibliography, user, "Q30000045", deprecated=True, redirectTo="Q30000044")

    result = manage_identity(client, "Q30000044", {"deprecateTo": "Q30000045"})

    assert result.status == falcon.HTTP_UNPROCESSABLE_ENTITY
    assert "redirect loop" in description(result)
    assert "deprecated" not in stored(database, "Q30000044")


def test_multi_record_cycle_is_rejected(client, database, bibliography, user):
    entry(bibliography, user, "Q30000046")
    entry(bibliography, user, "Q30000047", deprecated=True, redirectTo="Q30000046")
    entry(bibliography, user, "Q30000048", deprecated=True, redirectTo="Q30000047")

    result = manage_identity(client, "Q30000046", {"deprecateTo": "Q30000048"})

    assert result.status == falcon.HTTP_UNPROCESSABLE_ENTITY
    assert "redirect loop" in description(result)
    assert "deprecated" not in stored(database, "Q30000046")


def test_existing_valid_chain_is_accepted(client, database, bibliography, user):
    chain(bibliography, user, ["Q30000049", "Q30000050", "Q30000051"])
    entry(bibliography, user, "Q30000052")

    result = manage_identity(client, "Q30000052", {"deprecateTo": "Q30000049"})

    assert result.status == falcon.HTTP_OK
    assert bibliography.find("Q30000052")["id"] == "Q30000051"


def test_depth_violation_is_rejected(client, database, bibliography, user):
    ids = [f"Q3000006{index}" for index in range(MAX_REDIRECT_DEPTH + 1)]
    chain(bibliography, user, ids)
    entry(bibliography, user, "Q30000070")

    result = manage_identity(client, "Q30000070", {"deprecateTo": ids[0]})

    assert result.status == falcon.HTTP_UNPROCESSABLE_ENTITY
    assert "maximum depth" in description(result)
    assert "deprecated" not in stored(database, "Q30000070")


def test_reactivating_a_tombstone(client, database, bibliography, user):
    entry(bibliography, user, "Q30000071")
    entry(bibliography, user, "Q30000072", deprecated=True, redirectTo="Q30000071")

    result = manage_identity(client, "Q30000072", {"reactivate": True})

    assert result.status == falcon.HTTP_OK
    assert "deprecated" not in body(result)
    assert "redirectTo" not in body(result)
    assert "deprecated" not in stored(database, "Q30000072")
    assert bibliography.find("Q30000072")["id"] == "Q30000072"


def test_repairing_a_tombstone_target(client, database, bibliography, user):
    entry(bibliography, user, "Q30000073")
    entry(bibliography, user, "Q30000074")
    entry(bibliography, user, "Q30000075", deprecated=True, redirectTo="Q30000073")

    result = manage_identity(client, "Q30000075", {"deprecateTo": "Q30000074"})

    assert result.status == falcon.HTTP_OK
    assert stored(database, "Q30000075")["redirectTo"] == "Q30000074"
    assert bibliography.find("Q30000075")["id"] == "Q30000074"


def test_deprecate_and_reactivate_are_mutually_exclusive(
    client, database, bibliography, user
):
    entry(bibliography, user, "Q30000076")
    entry(bibliography, user, "Q30000077")

    result = manage_identity(
        client, "Q30000076", {"deprecateTo": "Q30000077", "reactivate": True}
    )

    assert result.status == falcon.HTTP_BAD_REQUEST
    assert "deprecated" not in stored(database, "Q30000076")


def test_deprecation_keeps_lookup_values_claimed(client, database, bibliography, user):
    entry(bibliography, user, "Q30000078", citationKey="kept1999Key")
    entry(bibliography, user, "Q30000079")

    manage_identity(client, "Q30000078", {"deprecateTo": "Q30000079"})

    assert bibliography.find("kept1999Key")["id"] == "Q30000079"
