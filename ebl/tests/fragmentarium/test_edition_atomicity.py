from typing import cast
from unittest.mock import patch

import falcon
import pytest
from falcon import testing
from pymongo.database import Database
from pymongo.errors import OperationFailure

from ebl.fragmentarium.application.fragment_updater import FragmentUpdater
from ebl.fragmentarium.domain.fragment import Fragment
from ebl.fragmentarium.domain.joins import Join
from ebl.fragmentarium.domain.transliteration_update import TransliterationUpdate
from ebl.fragmentarium.infrastructure.mongo_fragment_repository import (
    MongoFragmentRepository,
)
from ebl.tests.factories.fragment import FragmentFactory
from ebl.tests.fragmentarium.route_test_context import INVALID_MARKUP, RouteContext
from ebl.transliteration.domain.museum_number import MuseumNumber
from ebl.transliteration.domain.atf_parsers.lark_parser import parse_atf_lark
from ebl.users.domain.user import User


def stored_fragment(database: Database, fragment: Fragment) -> dict:
    return cast(dict, database["fragments"].find_one({"_id": str(fragment.number)}))


def test_rejected_combined_edition_keeps_storage_unchanged(
    route_context: RouteContext, fragment_repository: MongoFragmentRepository
) -> None:
    number = MuseumNumber.of("X.2")
    fragment = FragmentFactory.build(number=number)
    route_context.create(fragment)
    fragment_repository.create(FragmentFactory.build(number=MuseumNumber.of("X.1")))
    fragment_repository.create_join([[Join(number)], [Join(MuseumNumber.of("X.1"))]])
    original = stored_fragment(route_context.database, fragment)

    result = cast(
        testing.Result,
        route_context.post_edition(
            str(number),
            {
                "introduction": "Changed introduction",
                "notes": "Changed notes",
                "transliteration": "1. x",
            },
        ),
    )

    assert result.status == falcon.HTTP_UNPROCESSABLE_ENTITY
    assert "lowest" in cast(dict, result.json)["description"]
    assert stored_fragment(route_context.database, fragment) == original
    assert route_context.database["changelog"].count_documents({}) == 0


def test_rejected_notes_does_not_save_introduction(route_context: RouteContext) -> None:
    fragment = FragmentFactory.build()
    number = route_context.create(fragment)
    original = stored_fragment(route_context.database, fragment)

    result = cast(
        testing.Result,
        route_context.post_edition(
            number, {"introduction": "Valid introduction", "notes": INVALID_MARKUP}
        ),
    )

    assert result.status == falcon.HTTP_UNPROCESSABLE_ENTITY
    assert stored_fragment(route_context.database, fragment) == original
    assert route_context.database["changelog"].count_documents({}) == 0


@pytest.mark.parametrize(
    "updates",
    [
        {"introduction": "Changed introduction", "notes": "Changed notes"},
        {"introduction": "", "notes": "", "transliteration": "1. x"},
        {},
    ],
)
def test_combined_and_empty_editions_preserve_omitted_fields(
    route_context: RouteContext, updates: dict[str, str]
) -> None:
    fragment = FragmentFactory.build()
    number = route_context.create(fragment)
    original = stored_fragment(route_context.database, fragment)

    result = cast(testing.Result, route_context.post_edition(number, updates))

    assert result.status == falcon.HTTP_OK
    current = stored_fragment(route_context.database, fragment)
    for field in ("introduction", "notes"):
        assert current[field]["text"] == updates.get(field, original[field]["text"])
    assert current["text"] == (
        cast(dict, result.json)["text"]
        if "transliteration" in updates
        else original["text"]
    )
    assert route_context.database["changelog"].count_documents({}) == 1


def test_combined_edition_uses_one_document_update(
    fragment_repository: MongoFragmentRepository,
    fragment_updater: FragmentUpdater,
    user: User,
) -> None:
    fragment = FragmentFactory.build()
    fragment_repository.create(fragment)
    with patch.object(
        fragment_repository._fragments,
        "update_one",
        wraps=fragment_repository._fragments.update_one,
    ) as update:
        fragment_updater.update_edition(
            fragment.number, user, introduction="Introduction", notes="Notes"
        )

    assert update.call_count == 1
    assert set(update.call_args.args[1]["$set"]) == {"introduction", "notes"}


def test_batch_update_does_not_overwrite_unsupplied_concurrent_fields(
    fragment_repository: MongoFragmentRepository, database: Database
) -> None:
    fragment = FragmentFactory.build()
    fragment_repository.create(fragment)
    updated = fragment.set_introduction("Introduction").set_notes("Stale notes")
    concurrent_notes = fragment.set_notes("Concurrent notes")
    fragment_repository.update_field("notes", concurrent_notes)

    fragment_repository.update_fields(("introduction",), updated)

    current = stored_fragment(database, fragment)
    assert current["introduction"]["text"] == "Introduction"
    assert current["notes"]["text"] == "Concurrent notes"


def test_internal_combined_edition_can_ignore_lowest_join(
    fragment_repository: MongoFragmentRepository,
    fragment_updater: FragmentUpdater,
    user: User,
) -> None:
    number = MuseumNumber.of("X.2")
    fragment_repository.create(FragmentFactory.build(number=number))
    fragment_repository.create(FragmentFactory.build(number=MuseumNumber.of("X.1")))
    fragment_repository.create_join([[Join(number)], [Join(MuseumNumber.of("X.1"))]])

    fragment_updater.update_edition(
        number,
        user,
        introduction="Introduction",
        notes="Notes",
        transliteration=TransliterationUpdate(parse_atf_lark("1. x"), "X"),
        ignore_lowest_join=True,
    )

    current = fragment_repository.query_by_museum_number(number)
    assert current.introduction.text == "Introduction"
    assert current.notes.text == "Notes"
    assert current.text.atf == "1. x"


def test_batch_update_validates_all_fields_before_writing(
    fragment_repository: MongoFragmentRepository, database: Database
) -> None:
    fragment = FragmentFactory.build()
    fragment_repository.create(fragment)
    original = stored_fragment(database, fragment)

    with pytest.raises(ValueError, match="Unexpected update field"):
        fragment_repository.update_fields(
            ("introduction", "unknown"), fragment.set_introduction("Introduction")
        )

    assert stored_fragment(database, fragment) == original


def test_empty_batch_does_not_write(
    fragment_repository: MongoFragmentRepository,
) -> None:
    with patch.object(fragment_repository._fragments, "update_one") as update:
        fragment_repository.update_fields((), FragmentFactory.build())

    update.assert_not_called()


def test_failed_combined_persistence_does_not_write_changelog(
    fragment_repository: MongoFragmentRepository,
    fragment_updater: FragmentUpdater,
    database: Database,
    user: User,
) -> None:
    fragment = FragmentFactory.build()
    fragment_repository.create(fragment)
    original = stored_fragment(database, fragment)

    with patch.object(
        fragment_repository._fragments,
        "update_one",
        side_effect=OperationFailure("Failed"),
    ):
        with pytest.raises(OperationFailure):
            fragment_updater.update_edition(
                fragment.number, user, introduction="Introduction", notes="Notes"
            )

    assert stored_fragment(database, fragment) == original
    assert database["changelog"].count_documents({}) == 0
