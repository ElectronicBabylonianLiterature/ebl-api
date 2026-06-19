import pytest

from ebl.bibliography.application.duplicate_override import (
    DuplicateOverrideError,
    normalize_reviewed_candidate_ids,
)


@pytest.mark.parametrize("candidate_ids", [None, "A", [" "], []])
def test_normalize_reviewed_candidate_ids_rejects_invalid_values(candidate_ids) -> None:
    with pytest.raises(DuplicateOverrideError):
        normalize_reviewed_candidate_ids(candidate_ids)


def test_normalize_reviewed_candidate_ids_strips_and_deduplicates() -> None:
    assert normalize_reviewed_candidate_ids([" A ", "A", "B"]) == ["A", "B"]
