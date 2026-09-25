from ebl.tests.fragmentarium.fragment_repository_test_helpers import COLLECTION


def test_create_indexes_does_not_create_deferred_findspot_index(
    database, fragment_repository
):
    fragment_repository.create_indexes()

    fragment_index_keys = [
        index["key"] for index in database[COLLECTION].index_information().values()
    ]

    assert [("archaeology.findspotId", 1)] not in fragment_index_keys
