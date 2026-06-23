import json

import falcon
import pydash

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
    assert result.json["id"] != duplicate_entry["id"]
    assert result.json["citationKey"] == "miccadei2002Synergistic"
    assert result.json["aliases"] == [
        {
            "value": duplicate_entry["id"],
            "normalizedValue": duplicate_entry["id"].casefold(),
            "type": "partner_id",
            "source": "partner_request",
            "status": "redirect",
        }
    ]
    assert result.headers["Location"] == f"/api/v1/bibliography/{result.json['id']}"
    assert database["bibliography"].count_documents({}) == before_count + 1

    get_result = client.simulate_get(f"/api/v1/bibliography/{duplicate_entry['id']}")

    assert get_result.json["id"] == result.json["id"]
    assert get_result.json["bibliographyEntry"] == result.json


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
    assert result.json["id"] != proposed_entry["id"]
    assert result.json["citationKey"] == "miccadei2002Synergistic"
    assert result.headers["Location"] == f"/api/v1/bibliography/{result.json['id']}"
    assert database["bibliography"].count_documents({}) == before_count + 1


def test_partner_bibliography_duplicate_override_citation_key_collision_suffixes(
    monkeypatch, client, bibliography, user, database
):
    patch_duplicate_override_result(monkeypatch, insufficient_data_duplicate_result())
    existing_entry = BibliographyEntryFactory.build(
        id="Q30000000",
        citationKey="miccadei2002Synergistic",
    )
    bibliography.create(existing_entry, user)
    bibliography_entry = BibliographyEntryFactory.build(
        id="partner-override-123",
        type="book",
        DOI="10.1000/override-collision",
        PMID="99999998",
        title="Synergistic Tablets from Babylon",
        publisher="Test Press",
        volume="12",
        issue="1",
        page="1-20",
    )
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
    assert result.json["id"] != bibliography_entry["id"]
    assert result.json["citationKey"] == "miccadei2002Synergistic-2"
    assert result.headers["Location"] == f"/api/v1/bibliography/{result.json['id']}"
    assert result.json["aliases"] == [
        {
            "value": "partner-override-123",
            "normalizedValue": "partner-override-123",
            "type": "partner_id",
            "source": "partner_request",
            "status": "redirect",
        }
    ]
    assert database["bibliography"].count_documents({}) == before_count + 1
    assert bibliography.find(existing_entry["id"]) == existing_entry


def test_partner_bibliography_duplicate_override_without_id_generates_canonical_id(
    monkeypatch, client, database
):
    patch_duplicate_override_result(monkeypatch, insufficient_data_duplicate_result())
    bibliography_entry = pydash.omit(BibliographyEntryFactory.build(), "id")
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
    assert result.json["id"].startswith("Q")
    assert result.json["citationKey"] == "miccadei2002Synergistic"
    assert result.headers["Location"] == f"/api/v1/bibliography/{result.json['id']}"
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
    assert result.json["id"] != bibliography_entry["id"]
    assert result.headers["Location"] == f"/api/v1/bibliography/{result.json['id']}"
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
    assert result.json["id"] != bibliography_entry["id"]
    assert result.headers["Location"] == f"/api/v1/bibliography/{result.json['id']}"
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
    assert result.json["id"] != bibliography_entry["id"]
    assert result.json["citationKey"] == "miccadei2002Synergistic"
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
