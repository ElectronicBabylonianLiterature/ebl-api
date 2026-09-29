from ebl.bibliography.application.redirect_resolution import (
    follow_bibliography_redirect,
)


def test_a_tombstone_without_an_id_still_resolves_to_its_target() -> None:
    target = {"id": "TARGET", "type": "book"}

    resolved = follow_bibliography_redirect(
        {"deprecated": True, "redirectTo": "TARGET"}, {"TARGET": target}.__getitem__
    )

    assert resolved == target
