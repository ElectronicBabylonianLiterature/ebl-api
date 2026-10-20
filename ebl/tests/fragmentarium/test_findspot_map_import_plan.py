from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from pymongo import UpdateOne
from pymongo.errors import OperationFailure

from ebl.fragmentarium.application.findspot_map_location_importer_models import (
    MapLocationImportRecord,
)
from ebl.fragmentarium.application.findspot_map_location_importer_plan import (
    build_plan,
    write_operations,
)
from ebl.fragmentarium.application.map_location_schema import MapLocationSchema
from ebl.tests.fragmentarium.map_import_test_helpers import location


@pytest.mark.parametrize(
    "current,previous,expected",
    [
        (None, (), (0, 1, 0, 0)),
        ("new", (), (1, 0, 0, 0)),
        ("old", (), (0, 0, 1, 0)),
        ("old", ((1, "old"),), (0, 0, 1, 0)),
    ],
)
def test_forward_plan_preserves_accounting(
    current: str | None,
    previous: tuple[tuple[int, str], ...],
    expected: tuple[int, int, int, int],
) -> None:
    result = build_plan(
        (MapLocationImportRecord(1, location("new")),),
        {1: SimpleNamespace(map_location=location(current) if current else None)},
        False,
        tuple(
            MapLocationImportRecord(identifier, location(polygon))
            for identifier, polygon in previous
        ),
    )
    assert not result[0]
    assert result[1:5] == expected
    if result[3]:
        update = result[5][0]._doc
        assert isinstance(update, dict)
        assert update["$set"]["mapLocation"] == MapLocationSchema().dump(
            location("new")
        )
    if previous:
        assert result[5][0]._filter["mapLocation"] == MapLocationSchema().dump(
            location("old")
        )


@pytest.mark.parametrize(
    "current,previous,reason",
    [
        (None, ((1, "old"),), "expected previous mapLocation is missing"),
        (
            "other",
            ((1, "old"),),
            "existing mapLocation does not match previous artifact",
        ),
        ("other", ((2, "old"),), "unexpected mapLocation on newly mapped findspot"),
    ],
)
def test_forward_conflicts_do_not_create_operations(
    current: str | None, previous: tuple[tuple[int, str], ...], reason: str
) -> None:
    result = build_plan(
        (MapLocationImportRecord(1, location("new")),),
        {1: SimpleNamespace(map_location=location(current) if current else None)},
        False,
        tuple(
            MapLocationImportRecord(identifier, location(polygon))
            for identifier, polygon in previous
        ),
    )
    assert result[0][0].reason == reason
    assert result[5] == ()


@pytest.mark.parametrize(
    "current,previous,expected",
    [
        (None, (), (1, 0, 0, 0)),
        ("new", (), (0, 0, 1, 0)),
        ("other", (), (0, 0, 0, 1)),
        ("new", ((1, "old"),), (0, 0, 1, 0)),
        ("new", ((2, "old"),), (0, 0, 1, 0)),
        (None, ((2, "old"),), (1, 0, 0, 0)),
        ("old", ((1, "old"),), (1, 0, 0, 0)),
        ("other", ((1, "old"),), (0, 0, 0, 1)),
    ],
)
def test_rollback_changes_only_expected_current_values(
    current: str | None,
    previous: tuple[tuple[int, str], ...],
    expected: tuple[int, int, int, int],
) -> None:
    result = build_plan(
        (MapLocationImportRecord(1, location("new")),),
        {1: SimpleNamespace(map_location=location(current) if current else None)},
        True,
        tuple(
            MapLocationImportRecord(identifier, location(polygon))
            for identifier, polygon in previous
        ),
    )
    assert not result[0]
    assert result[1:5] == expected
    if result[5]:
        assert result[5][0]._filter["mapLocation"] == MapLocationSchema().dump(
            location("new")
        )
        update = result[5][0]._doc
        assert isinstance(update, dict)
        if previous == ((1, "old"),):
            assert update["$set"]["mapLocation"] == MapLocationSchema().dump(
                location("old")
            )
        else:
            assert update == {"$unset": {"mapLocation": ""}}


def test_transaction_success_uses_one_write() -> None:
    collection = MagicMock()
    collection.bulk_write.return_value.modified_count = 1
    operation = UpdateOne({"_id": 1}, {"$set": {"field": "value"}})
    assert write_operations(collection, (operation,)) == 1
    assert collection.bulk_write.call_count == 1
    assert "session" in collection.bulk_write.call_args.kwargs


def test_standalone_transactions_fall_back_once() -> None:
    collection = MagicMock()
    collection.bulk_write.side_effect = [
        OperationFailure(
            "Transaction numbers are only allowed on a replica set member or mongos",
            code=20,
        ),
        SimpleNamespace(modified_count=1),
    ]
    assert write_operations(collection, ()) == 1
    assert collection.bulk_write.call_count == 2
    assert "session" not in collection.bulk_write.call_args.kwargs


@pytest.mark.parametrize(
    "error",
    [
        OperationFailure("Unauthorized", code=13),
        OperationFailure("Unrelated illegal operation", code=20),
        RuntimeError("Uncertain outcome"),
    ],
)
def test_other_transaction_errors_are_never_replayed(error: Exception) -> None:
    collection = MagicMock()
    collection.bulk_write.side_effect = error
    with pytest.raises(type(error)):
        write_operations(collection, ())
    assert collection.bulk_write.call_count == 1


def test_commit_failure_never_replays_writes() -> None:
    collection = MagicMock()
    collection.bulk_write.return_value.modified_count = 1
    session = (
        collection.database.client.start_session.return_value.__enter__.return_value
    )
    transaction = session.start_transaction.return_value
    transaction.__exit__.side_effect = OperationFailure(
        "Transaction numbers are only allowed on a replica set member or mongos",
        code=20,
    )
    with pytest.raises(OperationFailure):
        write_operations(collection, ())
    assert collection.bulk_write.call_count == 1
