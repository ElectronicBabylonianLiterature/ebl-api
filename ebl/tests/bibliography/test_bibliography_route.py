import json

import attr
import falcon
import pydash
import pytest
from falcon import testing
from falcon_auth import NoneAuthBackend

import ebl.app
from ebl.tests.factories.bibliography import BibliographyEntryFactory
from ebl.users.infrastructure.auth0 import Auth0User

INVALID_ENTRIES = [
    lambda entry: {**entry, "title": 47},
    lambda entry: pydash.omit(entry, "type"),
]
BLOCKING_DUPLICATE_CANDIDATE_ID = "Q30000000"
NON_BLOCKING_DUPLICATE_CANDIDATE_ID = "Q30000002"
STALE_DUPLICATE_CANDIDATE_ID = "Q39999999"


@pytest.fixture
def saved_entry(bibliography, user):
    bibliography_entry = BibliographyEntryFactory.build()
    bibliography.create(bibliography_entry, user)
    return bibliography_entry


@pytest.fixture
def saved_entries(bibliography, user):
    number_of_entries = 5
    entries = [
        BibliographyEntryFactory.build(id=f"XY{i + 1:05}")
        for i in range(number_of_entries)
    ]

    for entry in entries:
        bibliography.create(entry, user)

    return entries


def client_with_scope(context, scope: str):
    return testing.TestClient(
        ebl.app.create_app(
            attr.evolve(
                context,
                auth_backend=NoneAuthBackend(
                    lambda: Auth0User({"scope": scope}, lambda: {"name": "Test User"})
                ),
            )
        )
    )


def duplicate_override_payload(bibliography_entry, reviewed_candidate_ids, reason=None):
    return {
        "bibliographyEntry": bibliography_entry,
        "override": {
            "reason": (
                reason
                or "Reviewed returned duplicate candidates and confirmed this is "
                "a distinct bibliography record."
            ),
            "reviewedCandidateIds": reviewed_candidate_ids,
        },
    }


def duplicate_override_candidate(id_, decision):
    return {
        "id": id_,
        "citationKey": None,
        "score": 0.95 if decision == "likely_duplicate" else 0.70,
        "decision": decision,
        "matchedFields": {},
        "conflictingFields": [],
        "evidenceCompleteness": 1.0,
        "recommendation": "block_or_request_override",
        "reason": "Test duplicate detection result.",
    }


def mixed_duplicate_override_result():
    return {
        "decision": "likely_duplicate",
        "highestScore": 0.95,
        "evidenceCompleteness": 1.0,
        "candidates": [
            duplicate_override_candidate(
                BLOCKING_DUPLICATE_CANDIDATE_ID, "likely_duplicate"
            ),
            duplicate_override_candidate(
                NON_BLOCKING_DUPLICATE_CANDIDATE_ID, "no_duplicate"
            ),
        ],
    }


def blocking_duplicate_override_result():
    return {
        "decision": "likely_duplicate",
        "highestScore": 0.95,
        "evidenceCompleteness": 1.0,
        "candidates": [
            duplicate_override_candidate(
                BLOCKING_DUPLICATE_CANDIDATE_ID, "likely_duplicate"
            )
        ],
    }


def patch_duplicate_override_result(monkeypatch, duplicate_result):
    monkeypatch.setattr(
        "ebl.bibliography.application.bibliography.Bibliography.find_duplicate_candidates",
        lambda self, entry, limit=10: duplicate_result,
    )


def assert_duplicate_override_bad_request(
    client, database, payload, *, description_substring=None
):
    before_count = database["bibliography"].count_documents({})
    result = client.simulate_post(
        "/api/v1/bibliography/duplicate-override",
        body=json.dumps(payload),
    )

    assert result.status == falcon.HTTP_BAD_REQUEST
    if description_substring is not None:
        assert description_substring in result.json["description"]
    assert database["bibliography"].count_documents({}) == before_count
    return result


def test_get_entry(client, saved_entry):
    id_ = saved_entry["id"]
    result = client.simulate_get(f"/bibliography/{id_}")

    assert result.json == saved_entry
    assert result.status == falcon.HTTP_OK


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


def test_list_bibliography(client, saved_entries):
    ids = [entry["id"] for entry in saved_entries]
    result = client.simulate_get(f"/bibliography/list?ids={','.join(ids)}")

    assert result.json == saved_entries
    assert result.status == falcon.HTTP_OK


def test_duplicate_candidates(client, database, saved_entry):
    proposed_entry = {**saved_entry, "id": "Q30000001"}
    before_count = database["bibliography"].count_documents({})

    result = client.simulate_post(
        "/api/v1/bibliography/duplicate-candidates",
        body=json.dumps(proposed_entry),
    )

    assert result.status == falcon.HTTP_OK
    assert result.json["decision"] == "likely_duplicate"
    assert result.json["highestScore"] >= 0.92
    assert result.json["candidates"][0]["id"] == saved_entry["id"]
    assert result.json["candidates"][0]["recommendation"] == "block_or_request_override"
    assert result.json["candidates"][0]["matchedFields"]["doi"] == 1.0
    assert database["bibliography"].count_documents({}) == before_count


def test_duplicate_candidates_allows_missing_id(client, saved_entry):
    proposed_entry = pydash.omit(saved_entry, "id")
    result = client.simulate_post(
        "/api/v1/bibliography/duplicate-candidates",
        body=json.dumps(proposed_entry),
    )

    assert result.status == falcon.HTTP_OK
    assert result.json["decision"] == "likely_duplicate"


def test_duplicate_candidates_series_sibling_is_not_likely(
    client, bibliography, user, database
):
    existing_entry = BibliographyEntryFactory.build(
        id="Q30000000",
        type="book",
        title="Babylonian Provincial Officials Part One",
        author=[{"given": "Mark", "family": "Smith"}],
        issued={"date-parts": [[2010]]},
        DOI="",
        publisher="Eisenbrauns",
        **{"collection-title": "Babylonian Provincial Officials"},
    )
    proposed_entry = {
        **existing_entry,
        "id": "Q30000001",
        "title": "Babylonian Provincial Officials Part Two",
    }
    bibliography.create(existing_entry, user)
    before_count = database["bibliography"].count_documents({})

    result = client.simulate_post(
        "/api/v1/bibliography/duplicate-candidates",
        body=json.dumps(proposed_entry),
    )

    assert result.status == falcon.HTTP_OK
    assert result.json["decision"] == "no_duplicate"
    assert result.json["candidates"][0]["decision"] == "no_duplicate"
    assert "series_part" in result.json["candidates"][0]["conflictingFields"]
    assert database["bibliography"].count_documents({}) == before_count


def test_duplicate_candidates_invalid(client):
    result = client.simulate_post(
        "/api/v1/bibliography/duplicate-candidates",
        body=json.dumps({"title": "Missing type"}),
    )

    assert result.status == falcon.HTTP_BAD_REQUEST


def test_duplicate_candidates_requires_duplicate_check_scope(guest_client, saved_entry):
    result = guest_client.simulate_post(
        "/api/v1/bibliography/duplicate-candidates",
        body=json.dumps(saved_entry),
    )

    assert result.status == falcon.HTTP_FORBIDDEN


def test_duplicate_candidates_rejects_write_only_scope(context, saved_entry):
    client = client_with_scope(context, "write:bibliography")
    result = client.simulate_post(
        "/api/v1/bibliography/duplicate-candidates",
        body=json.dumps(saved_entry),
    )

    assert result.status == falcon.HTTP_FORBIDDEN


def test_partner_bibliography_export_page(client, saved_entries):
    first_page = client.simulate_get("/api/v1/bibliography", params={"limit": 2})

    assert first_page.status == falcon.HTTP_OK
    assert first_page.json["limit"] == 2
    assert [item["id"] for item in first_page.json["items"]] == [
        saved_entries[0]["id"],
        saved_entries[1]["id"],
    ]
    assert first_page.json["items"][0]["citationKey"] is None
    assert first_page.json["items"][0]["bibliographyEntry"] == saved_entries[0]
    assert first_page.json["nextCursor"] == saved_entries[1]["id"]

    second_page = client.simulate_get(
        "/api/v1/bibliography",
        params={"limit": 2, "cursor": first_page.json["nextCursor"]},
    )

    assert [item["id"] for item in second_page.json["items"]] == [
        saved_entries[2]["id"],
        saved_entries[3]["id"],
    ]


def test_partner_bibliography_export_caps_limit(client, saved_entries):
    result = client.simulate_get("/api/v1/bibliography", params={"limit": 999})

    assert result.status == falcon.HTTP_OK
    assert result.json["limit"] == 100


def test_partner_bibliography_entry_by_id(client, saved_entry):
    result = client.simulate_get(f"/api/v1/bibliography/{saved_entry['id']}")

    assert result.status == falcon.HTTP_OK
    assert result.json["id"] == saved_entry["id"]
    assert result.json["citationKey"] is None
    assert result.json["bibliographyEntry"] == saved_entry


def test_partner_bibliography_entry_not_found(client):
    result = client.simulate_get("/api/v1/bibliography/not-found")

    assert result.status == falcon.HTTP_NOT_FOUND


def test_partner_bibliography_export_requires_export_scope(guest_client):
    result = guest_client.simulate_get("/api/v1/bibliography")

    assert result.status == falcon.HTTP_FORBIDDEN


def test_partner_bibliography_create(client):
    bibliography_entry = BibliographyEntryFactory.build(id="Q30000001")
    result = client.simulate_post(
        "/api/v1/bibliography", body=json.dumps(bibliography_entry)
    )

    assert result.status == falcon.HTTP_CREATED
    assert (
        result.headers["Location"] == f"/api/v1/bibliography/{bibliography_entry['id']}"
    )
    assert result.json == bibliography_entry

    get_result = client.simulate_get(f"/api/v1/bibliography/{bibliography_entry['id']}")

    assert get_result.json["bibliographyEntry"] == bibliography_entry


def test_partner_bibliography_create_requires_write_scope(guest_client):
    bibliography_entry = BibliographyEntryFactory.build(id="Q30000001")
    result = guest_client.simulate_post(
        "/api/v1/bibliography", body=json.dumps(bibliography_entry)
    )

    assert result.status == falcon.HTTP_FORBIDDEN


def test_partner_bibliography_create_rejects_export_only_scope(context):
    client = client_with_scope(context, "export:bibliography")
    bibliography_entry = BibliographyEntryFactory.build(id="Q30000001")
    result = client.simulate_post(
        "/api/v1/bibliography", body=json.dumps(bibliography_entry)
    )

    assert result.status == falcon.HTTP_FORBIDDEN


def test_partner_bibliography_create_invalid(client):
    result = client.simulate_post(
        "/api/v1/bibliography", body=json.dumps({"title": "Missing type"})
    )

    assert result.status == falcon.HTTP_BAD_REQUEST


def test_partner_bibliography_create_duplicate_conflict_does_not_mutate(
    client, database, saved_entry
):
    duplicate_entry = {**saved_entry, "id": "Q30000001"}
    before_count = database["bibliography"].count_documents({})

    result = client.simulate_post(
        "/api/v1/bibliography", body=json.dumps(duplicate_entry)
    )

    assert result.status == falcon.HTTP_CONFLICT
    assert result.json["decision"] == "likely_duplicate"
    assert result.json["candidates"][0]["id"] == saved_entry["id"]
    assert database["bibliography"].count_documents({}) == before_count


def test_partner_bibliography_duplicate_override_creates_likely_duplicate(
    client, database, saved_entry
):
    duplicate_entry = {**saved_entry, "id": "Q30000001"}
    before_count = database["bibliography"].count_documents({})

    result = client.simulate_post(
        "/api/v1/bibliography/duplicate-override",
        body=json.dumps(
            duplicate_override_payload(
                duplicate_entry, [saved_entry["id"], saved_entry["id"]]
            )
        ),
    )

    assert result.status == falcon.HTTP_CREATED
    assert result.headers["Location"] == "/api/v1/bibliography/Q30000001"
    assert result.json == duplicate_entry
    assert database["bibliography"].count_documents({}) == before_count + 1

    get_result = client.simulate_get("/api/v1/bibliography/Q30000001")

    assert get_result.json["bibliographyEntry"] == duplicate_entry


def test_partner_bibliography_duplicate_override_creates_possible_duplicate(
    client, bibliography, user, database
):
    existing_entry = BibliographyEntryFactory.build(
        id="Q30000000",
        type="article-journal",
        title="The Synergistic Activity of Thyroid Transcription Factor 1",
        author=[{"given": "Stefania", "family": "Miccadei"}],
        issued={"date-parts": [[1999, 1, 1]]},
        DOI="10.1210/MEND.16.4.0808",
        **{"container-title": "Molecular Endocrinology"},
        volume="2",
        issue="4",
        page="837-846",
    )
    proposed_entry = {**existing_entry, "id": "Q30000001"}
    proposed_entry["issued"] = {"date-parts": [[2002, 1, 1]]}
    bibliography.create(existing_entry, user)
    before_count = database["bibliography"].count_documents({})

    result = client.simulate_post(
        "/api/v1/bibliography/duplicate-override",
        body=json.dumps(
            duplicate_override_payload(proposed_entry, [existing_entry["id"]])
        ),
    )

    assert result.status == falcon.HTTP_CREATED
    assert result.headers["Location"] == "/api/v1/bibliography/Q30000001"
    assert result.json == proposed_entry
    assert database["bibliography"].count_documents({}) == before_count + 1


def test_partner_bibliography_duplicate_override_missing_override_does_not_mutate(
    client, database, saved_entry
):
    duplicate_entry = {**saved_entry, "id": "Q30000001"}
    assert_duplicate_override_bad_request(
        client,
        database,
        {"bibliographyEntry": duplicate_entry},
    )


def test_partner_bibliography_duplicate_override_whitespace_reason_does_not_mutate(
    client, database, saved_entry
):
    duplicate_entry = {**saved_entry, "id": "Q30000001"}
    assert_duplicate_override_bad_request(
        client,
        database,
        duplicate_override_payload(duplicate_entry, [saved_entry["id"]], "   "),
        description_substring="override.reason",
    )


def test_partner_bibliography_duplicate_override_short_reason_does_not_mutate(
    client, database, saved_entry
):
    duplicate_entry = {**saved_entry, "id": "Q30000001"}
    assert_duplicate_override_bad_request(
        client,
        database,
        duplicate_override_payload(duplicate_entry, [saved_entry["id"]], "too short"),
        description_substring="10 meaningful characters",
    )


@pytest.mark.parametrize(
    "payload",
    [
        lambda entry, candidate_id: {
            "bibliographyEntry": entry,
            "override": {"reason": "Reviewed returned duplicate candidates carefully."},
        },
        lambda entry, candidate_id: duplicate_override_payload(entry, []),
    ],
)
def test_partner_bibliography_duplicate_override_requires_reviewed_candidate_ids(
    payload, client, database, saved_entry
):
    duplicate_entry = {**saved_entry, "id": "Q30000001"}
    assert_duplicate_override_bad_request(
        client,
        database,
        payload(duplicate_entry, saved_entry["id"]),
    )


def test_partner_bibliography_duplicate_override_rejects_stale_candidate_ids(
    client, database, saved_entry
):
    duplicate_entry = {**saved_entry, "id": "Q30000001"}
    assert_duplicate_override_bad_request(
        client,
        database,
        duplicate_override_payload(duplicate_entry, ["Q39999999"]),
        description_substring="must match the current duplicate candidates",
    )


def test_partner_bibliography_duplicate_override_rejects_only_non_blocking_candidate_id(
    monkeypatch, client, database
):
    patch_duplicate_override_result(monkeypatch, mixed_duplicate_override_result())
    bibliography_entry = BibliographyEntryFactory.build(id="Q30000001")
    assert_duplicate_override_bad_request(
        client,
        database,
        duplicate_override_payload(
            bibliography_entry, [NON_BLOCKING_DUPLICATE_CANDIDATE_ID]
        ),
        description_substring="current blocking duplicate candidate",
    )


def test_partner_bibliography_duplicate_override_accepts_blocking_candidate_id(
    monkeypatch, client, database
):
    patch_duplicate_override_result(monkeypatch, mixed_duplicate_override_result())
    bibliography_entry = BibliographyEntryFactory.build(id="Q30000001")
    before_count = database["bibliography"].count_documents({})

    result = client.simulate_post(
        "/api/v1/bibliography/duplicate-override",
        body=json.dumps(
            duplicate_override_payload(
                bibliography_entry, [BLOCKING_DUPLICATE_CANDIDATE_ID]
            )
        ),
    )

    assert result.status == falcon.HTTP_CREATED
    assert result.headers["Location"] == "/api/v1/bibliography/Q30000001"
    assert result.json == bibliography_entry
    assert database["bibliography"].count_documents({}) == before_count + 1


def test_partner_bibliography_duplicate_override_accepts_blocking_with_non_blocking_id(
    monkeypatch, client, database
):
    patch_duplicate_override_result(monkeypatch, mixed_duplicate_override_result())
    bibliography_entry = BibliographyEntryFactory.build(id="Q30000001")
    before_count = database["bibliography"].count_documents({})

    result = client.simulate_post(
        "/api/v1/bibliography/duplicate-override",
        body=json.dumps(
            duplicate_override_payload(
                bibliography_entry,
                [
                    BLOCKING_DUPLICATE_CANDIDATE_ID,
                    NON_BLOCKING_DUPLICATE_CANDIDATE_ID,
                ],
            )
        ),
    )

    assert result.status == falcon.HTTP_CREATED
    assert result.headers["Location"] == "/api/v1/bibliography/Q30000001"
    assert result.json == bibliography_entry
    assert database["bibliography"].count_documents({}) == before_count + 1


def test_partner_bibliography_duplicate_override_rejects_stale_candidate_after_rerun(
    monkeypatch, client, database
):
    patch_duplicate_override_result(monkeypatch, blocking_duplicate_override_result())
    bibliography_entry = BibliographyEntryFactory.build(id="Q30000001")
    assert_duplicate_override_bad_request(
        client,
        database,
        duplicate_override_payload(bibliography_entry, [STALE_DUPLICATE_CANDIDATE_ID]),
        description_substring="must match the current duplicate candidates",
    )


def test_partner_bibliography_duplicate_override_reruns_duplicate_detection(
    client, bibliography, user, database
):
    existing_entry = BibliographyEntryFactory.build(
        id="Q30000000",
        DOI="10.1210/MEND.16.4.0808",
        title="The Synergistic Activity of Thyroid Transcription Factor 1",
        author=[{"given": "Stefania", "family": "Miccadei"}],
        issued={"date-parts": [[2002, 1, 1]]},
        **{"container-title": "Molecular Endocrinology"},
        volume="2",
        issue="4",
        page="837-846",
    )
    proposed_entry = {**existing_entry, "id": "Q30000001"}
    bibliography.create(existing_entry, user)

    preflight = client.simulate_post(
        "/api/v1/bibliography/duplicate-candidates",
        body=json.dumps(proposed_entry),
    )

    assert preflight.status == falcon.HTTP_OK
    assert preflight.json["candidates"][0]["id"] == existing_entry["id"]

    bibliography.update(
        {
            **existing_entry,
            "type": "book",
            "title": "Administrative Documents from Nippur",
            "author": [{"given": "Mary", "family": "Jones"}],
            "issued": {"date-parts": [[1971, 1, 1]]},
            "DOI": "",
            "ISBN": "9781575060727",
            "page": "1-50",
        },
        user,
    )
    before_count = database["bibliography"].count_documents({})

    result = client.simulate_post(
        "/api/v1/bibliography/duplicate-override",
        body=json.dumps(
            duplicate_override_payload(proposed_entry, [existing_entry["id"]])
        ),
    )

    assert result.status == falcon.HTTP_BAD_REQUEST
    assert "Use POST /api/v1/bibliography instead." in result.json["description"]
    assert database["bibliography"].count_documents({}) == before_count


def test_partner_bibliography_duplicate_override_unique_entry_uses_normal_create(
    client, database
):
    bibliography_entry = BibliographyEntryFactory.build(id="Q30000001")
    before_count = database["bibliography"].count_documents({})

    result = client.simulate_post(
        "/api/v1/bibliography/duplicate-override",
        body=json.dumps(duplicate_override_payload(bibliography_entry, ["Q39999999"])),
    )

    assert result.status == falcon.HTTP_BAD_REQUEST
    assert "Use POST /api/v1/bibliography instead." in result.json["description"]
    assert database["bibliography"].count_documents({}) == before_count


def test_partner_bibliography_duplicate_override_invalid_csl_does_not_mutate(
    client, database
):
    assert_duplicate_override_bad_request(
        client,
        database,
        {
            "bibliographyEntry": {"id": "Q30000001", "title": "Missing type"},
            "override": {
                "reason": (
                    "Reviewed returned duplicate candidates and confirmed this is "
                    "a distinct bibliography record."
                ),
                "reviewedCandidateIds": ["Q30000000"],
            },
        },
    )


def test_partner_bibliography_duplicate_override_requires_write_scope(
    guest_client, saved_entry
):
    duplicate_entry = {**saved_entry, "id": "Q30000001"}

    result = guest_client.simulate_post(
        "/api/v1/bibliography/duplicate-override",
        body=json.dumps(
            duplicate_override_payload(duplicate_entry, [saved_entry["id"]])
        ),
    )

    assert result.status == falcon.HTTP_FORBIDDEN


def test_partner_bibliography_duplicate_override_rejects_duplicate_check_only_scope(
    context, saved_entry
):
    client = client_with_scope(context, "check:bibliography_duplicates")
    duplicate_entry = {**saved_entry, "id": "Q30000001"}

    result = client.simulate_post(
        "/api/v1/bibliography/duplicate-override",
        body=json.dumps(
            duplicate_override_payload(duplicate_entry, [saved_entry["id"]])
        ),
    )

    assert result.status == falcon.HTTP_FORBIDDEN


def test_partner_bibliography_duplicate_override_rejects_export_only_scope(
    context, saved_entry
):
    client = client_with_scope(context, "export:bibliography")
    duplicate_entry = {**saved_entry, "id": "Q30000001"}

    result = client.simulate_post(
        "/api/v1/bibliography/duplicate-override",
        body=json.dumps(
            duplicate_override_payload(duplicate_entry, [saved_entry["id"]])
        ),
    )

    assert result.status == falcon.HTTP_FORBIDDEN


def test_partner_bibliography_create_series_sibling_does_not_conflict(
    client, bibliography, user
):
    existing_entry = BibliographyEntryFactory.build(
        id="Q30000000",
        type="book",
        title="Babylonian Provincial Officials Part One",
        author=[{"given": "Mark", "family": "Smith"}],
        issued={"date-parts": [[2010]]},
        DOI="",
        publisher="Eisenbrauns",
        **{"collection-title": "Babylonian Provincial Officials"},
    )
    sibling_entry = {
        **existing_entry,
        "id": "Q30000001",
        "title": "Babylonian Provincial Officials Part Two",
    }
    bibliography.create(existing_entry, user)

    result = client.simulate_post(
        "/api/v1/bibliography", body=json.dumps(sibling_entry)
    )

    assert result.status == falcon.HTTP_CREATED
    assert bibliography.find(existing_entry["id"]) == existing_entry
    assert bibliography.find(sibling_entry["id"]) == sibling_entry


def test_partner_bibliography_update(client, saved_entry):
    updated_entry = {**saved_entry, "title": "New Partner Title"}
    result = client.simulate_post(
        f"/api/v1/bibliography/{saved_entry['id']}", body=json.dumps(updated_entry)
    )

    assert result.status == falcon.HTTP_NO_CONTENT

    get_result = client.simulate_get(f"/api/v1/bibliography/{saved_entry['id']}")

    assert get_result.json["bibliographyEntry"] == updated_entry


def test_partner_bibliography_update_requires_write_scope(guest_client, saved_entry):
    updated_entry = {**saved_entry, "title": "New Partner Title"}
    result = guest_client.simulate_post(
        f"/api/v1/bibliography/{saved_entry['id']}", body=json.dumps(updated_entry)
    )

    assert result.status == falcon.HTTP_FORBIDDEN


def test_partner_bibliography_update_rejects_export_only_scope(context, saved_entry):
    client = client_with_scope(context, "export:bibliography")
    updated_entry = {**saved_entry, "title": "New Partner Title"}
    result = client.simulate_post(
        f"/api/v1/bibliography/{saved_entry['id']}", body=json.dumps(updated_entry)
    )

    assert result.status == falcon.HTTP_FORBIDDEN


def test_partner_bibliography_update_not_found(client):
    bibliography_entry = BibliographyEntryFactory.build(id="Q30000001")
    result = client.simulate_post(
        "/api/v1/bibliography/Q30000001", body=json.dumps(bibliography_entry)
    )

    assert result.status == falcon.HTTP_NOT_FOUND


def test_partner_bibliography_update_invalid(client, saved_entry):
    result = client.simulate_post(
        f"/api/v1/bibliography/{saved_entry['id']}",
        body=json.dumps(pydash.omit(saved_entry, "type")),
    )

    assert result.status == falcon.HTTP_BAD_REQUEST


def test_partner_bibliography_update_duplicate_conflict_does_not_mutate(
    client, bibliography, user
):
    existing_entry = BibliographyEntryFactory.build(id="Q30000001", DOI="10.1000/one")
    target_entry = BibliographyEntryFactory.build(id="Q30000002", DOI="10.1000/two")
    bibliography.create(existing_entry, user)
    bibliography.create(target_entry, user)
    duplicate_update = {**target_entry, "DOI": existing_entry["DOI"]}

    result = client.simulate_post(
        f"/api/v1/bibliography/{target_entry['id']}",
        body=json.dumps(duplicate_update),
    )

    assert result.status == falcon.HTTP_CONFLICT
    assert result.json["decision"] == "likely_duplicate"
    assert result.json["candidates"][0]["id"] == existing_entry["id"]
    assert bibliography.find(target_entry["id"]) == target_entry


def test_partner_bibliography_delete_not_supported(client, saved_entry):
    result = client.simulate_delete(f"/api/v1/bibliography/{saved_entry['id']}")

    assert result.status == falcon.HTTP_METHOD_NOT_ALLOWED
