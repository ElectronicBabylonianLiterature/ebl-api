import json

import falcon
import pydash
import pytest

from ebl.bibliography.application.bibliography import Bibliography
from ebl.tests.bibliography.bibliography_route_test_helpers import INVALID_ENTRIES
from ebl.tests.factories.bibliography import BibliographyEntryFactory


def test_get_entry(client, saved_entry):
    id_ = saved_entry["id"]
    result = client.simulate_get(f"/bibliography/{id_}")

    assert result.json == saved_entry
    assert result.status == falcon.HTTP_OK


def test_get_deprecated_entry_redirects_to_canonical(client, bibliography, user):
    canonical_entry = BibliographyEntryFactory.build(id="CANONICAL_ID")
    deprecated_entry = BibliographyEntryFactory.build(
        id="DUPLICATE_ID", deprecated=True, redirectTo=canonical_entry["id"]
    )
    bibliography.create(canonical_entry, user)
    bibliography.create(deprecated_entry, user)

    result = client.simulate_get(f"/bibliography/{deprecated_entry['id']}")

    assert result.status == falcon.HTTP_OK
    assert result.json == canonical_entry


def test_get_entry_not_found(client):
    result = client.simulate_get("/bibliography/not found")

    assert result.status == falcon.HTTP_NOT_FOUND


def test_create_entry(client):
    bibliography_entry = BibliographyEntryFactory.build()
    id_ = bibliography_entry["id"]
    body = json.dumps(bibliography_entry)
    post_result = client.simulate_post("/bibliography", body=body)

    assert post_result.status == falcon.HTTP_CREATED
    assert post_result.headers["Location"] == f"/bibliography/{id_}"
    assert post_result.json == bibliography_entry

    get_result = client.simulate_get(f"/bibliography/{id_}")

    assert get_result.json == bibliography_entry


def test_create_route_calls_the_guarded_application_method(client, monkeypatch):
    """`create_metadata` -- not the trusted `create` -- is what rejects
    server-owned fields for any caller, not just HTTP. Reverting the route to
    call `create` directly would remove that non-HTTP enforcement silently,
    since the route-level schema and hook alone would still reject the
    payloads the create-contract tests send.
    """
    calls = []
    monkeypatch.setattr(
        Bibliography,
        "create_metadata",
        lambda self, entry, user: calls.append(entry["id"]) or entry["id"],
    )
    bibliography_entry = BibliographyEntryFactory.build()

    result = client.simulate_post("/bibliography", body=json.dumps(bibliography_entry))

    assert result.status == falcon.HTTP_CREATED
    assert calls == [bibliography_entry["id"]]


def test_create_entry_duplicate(client, saved_entry):
    body = json.dumps(saved_entry)

    put_result = client.simulate_post("/bibliography", body=body)

    assert put_result.status == falcon.HTTP_CONFLICT


@pytest.mark.parametrize("transform", INVALID_ENTRIES)
def test_create_entry_invalid(transform, client):
    bibliography_entry = BibliographyEntryFactory.build()
    invalid_entry = transform(bibliography_entry)
    body = json.dumps(invalid_entry)

    put_result = client.simulate_post("/bibliography", body=body)

    assert put_result.status == falcon.HTTP_BAD_REQUEST


def test_create_rejects_lifecycle_state_outright(client):
    bibliography_entry = BibliographyEntryFactory.build(deprecated=True)

    result = client.simulate_post("/bibliography", json=bibliography_entry)

    assert result.status == falcon.HTTP_UNPROCESSABLE_ENTITY
    assert "deprecated" in result.text
    assert "identity" in result.text


def test_update_entry(client, saved_entry):
    id_ = saved_entry["id"]
    updated_entry = {**saved_entry, "title": "New Title"}
    body = json.dumps(updated_entry)
    post_result = client.simulate_post(f"/bibliography/{id_}", body=body)

    assert post_result.status == falcon.HTTP_NO_CONTENT

    get_result = client.simulate_get(f"/bibliography/{id_}")

    assert get_result.json == updated_entry


def test_update_entry_not_found(client):
    bibliography_entry = BibliographyEntryFactory.build()
    id_ = bibliography_entry["id"]
    body = json.dumps(bibliography_entry)

    post_result = client.simulate_post(f"/bibliography/{id_}", body=body)

    assert post_result.status == falcon.HTTP_NOT_FOUND


@pytest.mark.parametrize(
    "transform",
    [lambda entry: {**entry, "title": 47}, lambda entry: pydash.omit(entry, "type")],
)
def test_update_entry_invalid(transform, client, saved_entry):
    id_ = saved_entry["id"]
    invalid_entry = transform(saved_entry)
    body = json.dumps(invalid_entry)

    post_result = client.simulate_post(f"/bibliography/{id_}", body=body)

    assert post_result.status == falcon.HTTP_BAD_REQUEST


@pytest.mark.parametrize(
    "params",
    [
        {"query": "Miccadei"},
        {
            "query": "Miccadei 2002 The Synergistic Activity of Thyroid Transcription Factor 1"
        },
        {"query": "ME 1"},
        {"query": "ME"},
    ],
)
def test_search(client, saved_entry, params):
    result = client.simulate_get("/bibliography", params=params)

    assert result.json == [saved_entry]
    assert result.status == falcon.HTTP_OK


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


def test_update_entry_rejects_a_non_object_body(client, saved_entry):
    result = client.simulate_post(
        f"/bibliography/{saved_entry['id']}", body=json.dumps([saved_entry])
    )

    assert result.status == falcon.HTTP_BAD_REQUEST


def test_list_bibliography_serves_the_cached_response(
    cached_client, bibliography, user
):
    entry = BibliographyEntryFactory.build(id="Q30000123")
    bibliography.create(entry, user)
    url = "/bibliography/list"

    first_result = cached_client.simulate_get(url, params={"ids": entry["id"]})
    second_result = cached_client.simulate_get(url, params={"ids": entry["id"]})

    assert first_result.status == falcon.HTTP_OK
    assert second_result.json == first_result.json
