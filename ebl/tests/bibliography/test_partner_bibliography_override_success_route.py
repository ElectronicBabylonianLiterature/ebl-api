import json

import falcon

from ebl.tests.bibliography.bibliography_route_test_helpers import (
    BLOCKING_DUPLICATE_CANDIDATE_ID,
    INSUFFICIENT_DATA_DUPLICATE_CANDIDATE_ID,
    NON_BLOCKING_DUPLICATE_CANDIDATE_ID,
    duplicate_override_payload,
    insufficient_data_duplicate_result,
    mixed_duplicate_override_result,
    patch_duplicate_override_result,
)
from ebl.tests.factories.bibliography import BibliographyEntryFactory


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


def test_partner_bibliography_duplicate_override_creates_insufficient_data(
    monkeypatch, client, database
):
    patch_duplicate_override_result(monkeypatch, insufficient_data_duplicate_result())
    bibliography_entry = BibliographyEntryFactory.build(id="Q30000001")
    before_count = database["bibliography"].count_documents({})

    result = client.simulate_post(
        "/api/v1/bibliography/duplicate-override",
        body=json.dumps(
            duplicate_override_payload(
                bibliography_entry, [INSUFFICIENT_DATA_DUPLICATE_CANDIDATE_ID]
            )
        ),
    )

    assert result.status == falcon.HTTP_CREATED
    assert result.json == bibliography_entry
    assert database["bibliography"].count_documents({}) == before_count + 1


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
