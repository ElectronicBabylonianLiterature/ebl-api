from ebl.tests.fragmentarium.fragment_repository_test_helpers import COLLECTION
from ebl.fragmentarium.infrastructure.mongo_fragment_repository import (
    MongoFragmentRepository,
)
from pymongo.database import Database


def test_create_indexes_creates_findspot_query_index(
    database: Database, fragment_repository: MongoFragmentRepository
) -> None:
    fragment_repository.create_indexes()

    fragment_index_keys = [
        index["key"] for index in database[COLLECTION].index_information().values()
    ]

    assert [("archaeology.findspotId", 1)] in fragment_index_keys
