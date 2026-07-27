import pytest

from ebl.tests.fragmentarium.route_test_context import (
    RouteContext,
    assert_edition_field_updated,
    assert_invalid_edition_field,
)
from ebl.tests.fragmentarium.transliterations_route_test_helpers import NOTES_FIXTURE


@pytest.mark.parametrize("notes", NOTES_FIXTURE)
def test_update_notes(route_context: RouteContext, notes):
    old_notes, new_notes = notes

    assert_edition_field_updated(route_context, "notes", old_notes, new_notes)


def test_update_invalid_notes(route_context: RouteContext):
    assert_invalid_edition_field(route_context, "notes")
