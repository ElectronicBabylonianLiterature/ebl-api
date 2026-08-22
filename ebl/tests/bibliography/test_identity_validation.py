import pytest

from ebl.bibliography.application.identity_validation import validate_identity_state
from ebl.errors import DataError, NotFoundError

ACTIVE = {"id": "Q1", "type": "book"}


def records(*entries):
    stored = {entry["id"]: entry for entry in entries}

    def query_by_id(id_: str) -> dict:
        if id_ not in stored:
            raise NotFoundError(f"bibliography {id_} not found.")
        return dict(stored[id_])

    def query_by_redirect_target(id_: str) -> list[dict]:
        return [
            dict(candidate)
            for candidate in stored.values()
            if candidate.get("redirectTo") == id_
        ]

    return query_by_id, query_by_redirect_target


def test_active_entry_is_valid():
    validate_identity_state(ACTIVE, *records())


def test_valid_tombstone_is_accepted():
    entry = {**ACTIVE, "deprecated": True, "redirectTo": "Q2"}

    validate_identity_state(entry, *records({"id": "Q2", "type": "book"}))


def test_deprecated_without_a_target_raises():
    entry = {**ACTIVE, "deprecated": True}

    with pytest.raises(DataError, match="without a redirect target"):
        validate_identity_state(entry, *records())


def test_deprecated_with_an_empty_target_raises():
    entry = {**ACTIVE, "deprecated": True, "redirectTo": ""}

    with pytest.raises(DataError, match="without a redirect target"):
        validate_identity_state(entry, *records())


def test_deprecated_with_a_non_string_target_raises():
    entry = {**ACTIVE, "deprecated": True, "redirectTo": 7}

    with pytest.raises(DataError, match="without a redirect target"):
        validate_identity_state(entry, *records())


def test_self_redirect_raises():
    entry = {**ACTIVE, "deprecated": True, "redirectTo": "Q1"}

    with pytest.raises(DataError, match="cannot redirect to itself"):
        validate_identity_state(entry, *records())


def test_redirect_target_without_deprecation_raises():
    entry = {**ACTIVE, "redirectTo": "Q2"}

    with pytest.raises(DataError, match="while it is not deprecated"):
        validate_identity_state(entry, *records({"id": "Q2", "type": "book"}))


def test_missing_target_raises_a_data_error():
    entry = {**ACTIVE, "deprecated": True, "redirectTo": "Q2"}

    with pytest.raises(DataError, match="Q2 not found"):
        validate_identity_state(entry, *records())


def test_cycle_raises_a_data_error():
    entry = {**ACTIVE, "deprecated": True, "redirectTo": "Q2"}
    query = records(
        {"id": "Q2", "type": "book", "deprecated": True, "redirectTo": "Q1"}
    )

    with pytest.raises(DataError, match="redirect loop"):
        validate_identity_state(entry, *query)


def test_depth_violation_raises_a_data_error():
    entry = {**ACTIVE, "deprecated": True, "redirectTo": "Q2"}
    chain = [
        {
            "id": f"Q{index}",
            "type": "book",
            "deprecated": True,
            "redirectTo": f"Q{index + 1}",
        }
        for index in range(2, 9)
    ]

    with pytest.raises(DataError, match="maximum depth"):
        validate_identity_state(entry, *records(*chain, {"id": "Q9", "type": "book"}))


def test_the_prospective_entry_is_used_instead_of_the_stored_one():
    entry = {**ACTIVE, "deprecated": True, "redirectTo": "Q2"}
    stale = {"id": "Q1", "type": "book", "deprecated": True, "redirectTo": "Q9"}

    validate_identity_state(entry, *records(stale, {"id": "Q2", "type": "book"}))


def test_inbound_predecessor_depth_violation_raises_a_data_error():
    """Q1's own forward walk (5 hops) is within the limit, but an existing
    predecessor X -> Q1 would need 6 -- only the inbound check catches this.
    """
    entry = {**ACTIVE, "deprecated": True, "redirectTo": "Q2"}
    forward_chain = [
        {
            "id": f"Q{index}",
            "type": "book",
            "deprecated": True,
            "redirectTo": f"Q{index + 1}",
        }
        for index in range(2, 6)
    ]
    predecessor = {"id": "X", "type": "book", "deprecated": True, "redirectTo": "Q1"}

    with pytest.raises(DataError, match="maximum depth"):
        validate_identity_state(
            entry,
            *records(*forward_chain, {"id": "Q6", "type": "book"}, predecessor),
        )


def test_inbound_predecessor_within_the_limit_is_accepted():
    entry = {**ACTIVE, "deprecated": True, "redirectTo": "Q2"}
    predecessor = {"id": "X", "type": "book", "deprecated": True, "redirectTo": "Q1"}

    validate_identity_state(entry, *records({"id": "Q2", "type": "book"}, predecessor))
