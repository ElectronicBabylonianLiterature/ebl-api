from ebl.bibliography.application.redirect_resolution import (
    follow_bibliography_redirect,
)


def test_redirect_resolution_tolerates_a_legacy_non_string_id() -> None:
    canonical = {"id": "CANONICAL", "type": "book"}

    result = follow_bibliography_redirect(
        {"id": 47, "deprecated": True, "redirectTo": "CANONICAL"},
        lambda _id: canonical,
    )

    assert result == canonical
