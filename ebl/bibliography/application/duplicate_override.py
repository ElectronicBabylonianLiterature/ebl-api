from __future__ import annotations

from typing import Any, Mapping, Sequence

BLOCKING_DUPLICATE_DECISIONS = {
    "likely_duplicate",
    "possible_duplicate",
    "insufficient_data",
}
MIN_DUPLICATE_OVERRIDE_REASON_LENGTH = 10


class DuplicateOverrideError(Exception):
    pass


def validate_duplicate_override(
    override: Mapping[str, Any], duplicate_result: Mapping[str, Any]
) -> None:
    validate_override_reason(override.get("reason"))
    reviewed_candidate_ids = normalize_reviewed_candidate_ids(
        override.get("reviewedCandidateIds")
    )
    current_candidate_ids = {
        candidate["id"] for candidate in duplicate_result["candidates"]
    }
    blocking_candidate_ids = blocking_duplicate_candidate_ids(duplicate_result)
    if any(
        candidate_id not in current_candidate_ids
        for candidate_id in reviewed_candidate_ids
    ):
        raise DuplicateOverrideError(
            "override.reviewedCandidateIds must match the current duplicate "
            "candidates returned by the server-side rerun."
        )
    if not set(reviewed_candidate_ids).intersection(blocking_candidate_ids):
        raise DuplicateOverrideError(
            "override.reviewedCandidateIds must include at least one current "
            "blocking duplicate candidate."
        )


def validate_override_reason(reason: Any) -> None:
    if not isinstance(reason, str) or not reason.strip():
        raise DuplicateOverrideError("override.reason must be a non-empty string.")
    if len("".join(reason.split())) < MIN_DUPLICATE_OVERRIDE_REASON_LENGTH:
        raise DuplicateOverrideError(
            "override.reason must contain at least 10 meaningful characters."
        )


def blocking_duplicate_candidate_ids(
    duplicate_result: Mapping[str, Any],
) -> set[str]:
    return {
        candidate["id"]
        for candidate in duplicate_result["candidates"]
        if candidate["decision"] in BLOCKING_DUPLICATE_DECISIONS
    }


def normalize_reviewed_candidate_ids(candidate_ids: Any) -> Sequence[str]:
    if not isinstance(candidate_ids, Sequence) or isinstance(
        candidate_ids, (str, bytes)
    ):
        raise_reviewed_candidate_ids_error()

    normalized_candidate_ids = []
    for candidate_id in candidate_ids:
        if not isinstance(candidate_id, str) or not candidate_id.strip():
            raise_reviewed_candidate_ids_error()
        normalized_candidate_ids.append(candidate_id.strip())

    deduplicated_candidate_ids = list(dict.fromkeys(normalized_candidate_ids))
    if not deduplicated_candidate_ids:
        raise_reviewed_candidate_ids_error()
    return deduplicated_candidate_ids


def raise_reviewed_candidate_ids_error() -> None:
    raise DuplicateOverrideError(
        "override.reviewedCandidateIds must be a non-empty array of strings."
    )
