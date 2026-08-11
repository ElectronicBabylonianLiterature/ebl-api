import pytest
from freezegun import freeze_time

from ebl.fragmentarium.domain.fragment import Fragment
from ebl.fragmentarium.domain.transliteration_update import TransliterationUpdate
from ebl.tests.factories.fragment import FragmentFactory
from ebl.tests.fragmentarium.route_test_context import (
    RouteContext,
    assert_edition_field_updated,
    assert_invalid_edition_field,
)
from ebl.transliteration.domain.atf_parsers.lark_parser import parse_atf_lark
from ebl.tests.fragmentarium.transliterations_route_test_helpers import (
    INTRO_FIXTURE,
    NOTES_FIXTURE,
)
import falcon


@pytest.mark.parametrize("introduction", INTRO_FIXTURE)
def test_update_introduction(route_context: RouteContext, introduction):
    old_introduction, new_introduction = introduction

    assert_edition_field_updated(
        route_context, "introduction", old_introduction, new_introduction
    )


def test_update_invalid_introduction(route_context: RouteContext):
    assert_invalid_edition_field(route_context, "introduction")


@pytest.mark.parametrize("introduction", INTRO_FIXTURE)
@pytest.mark.parametrize("notes", NOTES_FIXTURE)
@pytest.mark.parametrize("new_transliteration", ["", "$ (the transliteration)"])
@freeze_time("2018-09-07 15:41:24.032")
def test_update_multiple_fields(
    route_context: RouteContext, introduction, notes, new_transliteration
):
    old_introduction, new_introduction = introduction
    old_notes, new_notes = notes
    fragment: Fragment = FragmentFactory.build(
        introduction=old_introduction, notes=old_notes
    )
    number = route_context.create(fragment)
    updates = {
        "introduction": new_introduction.text,
        "notes": new_notes.text,
        "transliteration": new_transliteration,
    }

    post_result = route_context.post_edition(number, updates)
    expected_json = route_context.expect_dto(
        fragment.set_introduction(new_introduction.text)
        .set_notes(new_notes.text)
        .update_transliteration(
            TransliterationUpdate(parse_atf_lark(updates["transliteration"])),
            route_context.user,
        )
    )

    assert post_result.status == falcon.HTTP_OK
    assert post_result.json == expected_json
    assert route_context.get_fragment(number).json == {
        **expected_json,
        "realiaInfo": [],
    }
    assert route_context.has_changelog_entry(number)
