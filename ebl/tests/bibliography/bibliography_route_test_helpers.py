import json

import attr
import falcon
import pydash
from falcon import testing
from falcon_auth import NoneAuthBackend

import ebl.app
from ebl.users.infrastructure.auth0 import Auth0User

INVALID_ENTRIES = [
    lambda entry: {**entry, "title": 47},
    lambda entry: pydash.omit(entry, "type"),
]
BLOCKING_DUPLICATE_CANDIDATE_ID = "Q30000000"
INSUFFICIENT_DATA_DUPLICATE_CANDIDATE_ID = "Q30000003"
NON_BLOCKING_DUPLICATE_CANDIDATE_ID = "Q30000002"
STALE_DUPLICATE_CANDIDATE_ID = "Q39999999"


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


def insufficient_data_duplicate_result():
    return {
        "decision": "insufficient_data",
        "highestScore": 0.75,
        "evidenceCompleteness": 0.25,
        "candidates": [
            {
                **duplicate_override_candidate(
                    INSUFFICIENT_DATA_DUPLICATE_CANDIDATE_ID, "insufficient_data"
                ),
                "recommendation": "confirm_before_create",
            }
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
