from pymongo.database import Database

from ebl.bibliography.application.lookup_reservation import (
    LookupReservationOperation,
    LookupReservationState,
)
from ebl.bibliography.infrastructure.bibliography import MongoBibliographyRepository
from ebl.tests.bibliography.lookup_reservation_test_helpers import (
    COLLECTION,
    LATER,
    NOW,
)
from ebl.tests.factories.bibliography import BibliographyEntryFactory


def test_container_query_accepts_only_a_collection_number(
    bibliography_repository: MongoBibliographyRepository,
) -> None:
    entry = {
        **BibliographyEntryFactory.build(id="Q30000180"),
        "container-title-short": "Container",
        "collection-number": "42",
    }
    bibliography_repository.create(entry)

    assert bibliography_repository.query_by_container_title_and_collection_number(
        None, "42"
    ) == [entry]


def test_title_query_accepts_only_a_volume(
    bibliography_repository: MongoBibliographyRepository,
) -> None:
    entry = BibliographyEntryFactory.build(
        id="Q30000181", **{"title-short": "Title", "volume": "7"}
    )
    bibliography_repository.create(entry)

    assert bibliography_repository.query_by_title_short_and_volume(None, "7") == [entry]


def test_reconciliation_checks_a_lookup_value_that_cannot_be_normalized(
    database: Database,
    bibliography_repository: MongoBibliographyRepository,
    create_mongo_bibliography_entry,
) -> None:
    value = "𒀭"
    bibliography_repository.claim_lookup_values(
        LookupReservationOperation("owner", "Q30000182", NOW), [value]
    )
    database["bibliography"].insert_one(
        create_mongo_bibliography_entry(
            {
                "id": "Q30000182",
                "type": "book",
                "aliases": [{"value": value}],
            }
        )
    )

    bibliography_repository.reconcile_lookup_reservations(LATER)

    reservation = database[COLLECTION].find_one({"_id": value})
    assert reservation is not None
    assert reservation["state"] == LookupReservationState.COMMITTED.value
