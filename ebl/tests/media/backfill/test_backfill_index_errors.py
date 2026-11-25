from collections.abc import Callable
from unittest.mock import Mock

import pytest
from pymongo.collection import Collection
from pymongo.database import Database
from pymongo.errors import OperationFailure

from ebl.media.infrastructure.backfill_preflight import prepare_legacy_indexes


def test_index_preparation_preserves_unrelated_driver_failures(
    database: Database, legacy_photo: Callable, monkeypatch: pytest.MonkeyPatch
) -> None:
    legacy_photo()
    database["photos.files"].drop_indexes()
    failure = OperationFailure("permission denied", code=13)
    monkeypatch.setattr(Collection, "create_index", Mock(side_effect=failure))
    with pytest.raises(OperationFailure) as caught:
        prepare_legacy_indexes(database)
    assert caught.value is failure
