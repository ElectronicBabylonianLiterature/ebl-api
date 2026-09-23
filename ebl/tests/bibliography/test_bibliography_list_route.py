import falcon

from ebl.tests.bibliography.identity_management_test_helpers import (
    admin_client,
    alias,
    manage_identity,
)
from ebl.tests.factories.bibliography import BibliographyEntryFactory


def test_list_all_bibliography(client, saved_entry):
    result = client.simulate_get("/bibliography/all")

    assert result.json == [saved_entry["id"]]
    assert result.status == falcon.HTTP_OK


def test_list_all_bibliography_excludes_deprecated(client, bibliography, user):
    canonical_entry = BibliographyEntryFactory.build(id="CANONICAL_ID")
    deprecated_entry = BibliographyEntryFactory.build(
        id="DUPLICATE_ID", deprecated=True, redirectTo=canonical_entry["id"]
    )
    bibliography.create(canonical_entry, user)
    bibliography.create(deprecated_entry, user)

    result = client.simulate_get("/bibliography/all")

    assert result.status == falcon.HTTP_OK
    assert result.json == [canonical_entry["id"]]


def test_list_bibliography(client, saved_entries):
    ids = [entry["id"] for entry in saved_entries]
    result = client.simulate_get(f"/bibliography/list?ids={','.join(ids)}")

    assert result.json == saved_entries
    assert result.status == falcon.HTTP_OK


def test_list_bibliography_resolves_deprecated_ids(client, bibliography, user):
    canonical_entry = BibliographyEntryFactory.build(id="CANONICAL_ID")
    deprecated_entry = BibliographyEntryFactory.build(
        id="DUPLICATE_ID", deprecated=True, redirectTo=canonical_entry["id"]
    )
    bibliography.create(canonical_entry, user)
    bibliography.create(deprecated_entry, user)

    result = client.simulate_get(
        "/bibliography/list", params={"ids": deprecated_entry["id"]}
    )

    assert result.status == falcon.HTTP_OK
    assert result.json == [canonical_entry]


def test_list_bibliography_deduplicates_redirected_canonical_entries(
    client, bibliography, user
):
    canonical_entry = BibliographyEntryFactory.build(id="CANONICAL_ID")
    deprecated_entry = BibliographyEntryFactory.build(
        id="DUPLICATE_ID", deprecated=True, redirectTo=canonical_entry["id"]
    )
    bibliography.create(canonical_entry, user)
    bibliography.create(deprecated_entry, user)

    result = client.simulate_get(
        "/bibliography/list",
        params={"ids": f"{deprecated_entry['id']},{canonical_entry['id']}"},
    )

    assert result.status == falcon.HTTP_OK
    assert result.json == [canonical_entry]


def test_list_bibliography_skips_an_entry_with_a_broken_redirect(
    client, database, bibliography, user
):
    valid_entry = BibliographyEntryFactory.build(id="VALID_ID")
    bibliography.create(valid_entry, user)
    for loop_id, target in (("LOOP_A", "LOOP_B"), ("LOOP_B", "LOOP_A")):
        bibliography.create(BibliographyEntryFactory.build(id=loop_id), user)
        database["bibliography"].update_one(
            {"_id": loop_id},
            {"$set": {"deprecated": True, "redirectTo": target}},
        )

    result = client.simulate_get(
        "/bibliography/list", params={"ids": f"LOOP_A,{valid_entry['id']}"}
    )

    assert result.status == falcon.HTTP_OK
    assert result.json == [valid_entry]


def test_list_bibliography_handles_canonical_alias_unknown_and_broken_ids(
    client, context, database, bibliography, user
):
    canonical_entry = BibliographyEntryFactory.build(id="CANONICAL_ID")
    aliased_entry = BibliographyEntryFactory.build(id="ALIASED_ID")
    broken_entry = BibliographyEntryFactory.build(id="BROKEN_ID")
    for entry in (canonical_entry, aliased_entry, broken_entry):
        bibliography.create(entry, user)
    identity_result = manage_identity(
        admin_client(context),
        aliased_entry["id"],
        {"addAliases": [alias("legacy-alias")]},
    )
    database["bibliography"].update_one(
        {"_id": broken_entry["id"]},
        {"$set": {"deprecated": True, "redirectTo": "MISSING_ID"}},
    )

    result = client.simulate_get(
        "/bibliography/list",
        params={"ids": f"{canonical_entry['id']},legacy-alias,UNKNOWN_ID,BROKEN_ID"},
    )

    assert identity_result.status == falcon.HTTP_OK
    assert result.status == falcon.HTTP_OK
    assert result.json == [canonical_entry]


def test_list_bibliography_does_not_suppress_a_systemic_query_failure(
    monkeypatch, client, bibliography_repository
):
    def fail_query(_ids):
        raise RuntimeError("batch query failed")

    monkeypatch.setattr(bibliography_repository, "query_by_ids", fail_query)

    result = client.simulate_get("/bibliography/list", params={"ids": "Q30000000"})

    assert result.status == falcon.HTTP_INTERNAL_SERVER_ERROR


def test_list_bibliography_returns_a_consistent_response(
    cached_client, bibliography, user
):
    entry = BibliographyEntryFactory.build(id="Q30000123")
    bibliography.create(entry, user)
    url = "/bibliography/list"

    first_result = cached_client.simulate_get(url, params={"ids": entry["id"]})
    second_result = cached_client.simulate_get(url, params={"ids": entry["id"]})

    assert first_result.status == falcon.HTTP_OK
    assert second_result.json == first_result.json


def test_metadata_update_does_not_serve_a_stale_cached_batch_entry(
    cached_client, bibliography, user
):
    entry = BibliographyEntryFactory.build(id="Q30000123", title="Old title")
    bibliography.create(entry, user)
    url = "/bibliography/list"
    cached_client.simulate_get(url, params={"ids": entry["id"]})

    update_result = cached_client.simulate_post(
        f"/bibliography/{entry['id']}", json={**entry, "title": "New title"}
    )
    result = cached_client.simulate_get(url, params={"ids": entry["id"]})

    assert update_result.status == falcon.HTTP_NO_CONTENT
    assert result.json[0]["title"] == "New title"
