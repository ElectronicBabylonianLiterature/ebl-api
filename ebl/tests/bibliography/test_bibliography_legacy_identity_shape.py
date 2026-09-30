import falcon
import pytest

from ebl.bibliography.application.serialization import create_mongo_entry
from ebl.tests.bibliography.identity_preservation_test_helpers import (
    CORRECTED_TITLE,
    metadata_only_payload,
    post_entry,
    reservations,
)
from ebl.tests.factories.bibliography import BibliographyEntryFactory

CANONICAL_ID = "rla_9_388"
LOSER_ID = "RN2001"
MISSING_LOSER_ID = "RN9999"


def legacy_alias(value: str, normalized_value: str) -> dict:
    return {
        "value": value,
        "normalizedValue": normalized_value,
        "type": "legacy_id",
        "source": "duplicate_merge_2026-08-04",
        "status": "redirect",
    }


def seed(database, id_: str, **fields) -> dict:
    entry = BibliographyEntryFactory.build(id=id_)
    database["bibliography"].insert_one({**create_mongo_entry(entry), **fields})
    return entry


def stored(database, id_: str) -> dict:
    return database["bibliography"].find_one({"_id": id_})


@pytest.fixture
def merged_pair(database):
    canonical = seed(
        database,
        CANONICAL_ID,
        aliases=[legacy_alias(LOSER_ID, "rn2001")],
    )
    seed(database, LOSER_ID, deprecated=True, redirectTo=CANONICAL_ID)
    return canonical


@pytest.fixture
def alias_only_canonical(database):
    return seed(
        database,
        CANONICAL_ID,
        aliases=[legacy_alias(MISSING_LOSER_ID, "rn9999")],
    )


def test_merged_canonical_metadata_update_succeeds(client, database, merged_pair):
    result = post_entry(client, metadata_only_payload(merged_pair))

    assert result.status == falcon.HTTP_NO_CONTENT
    assert stored(database, CANONICAL_ID)["title"] == CORRECTED_TITLE


def test_merged_canonical_update_keeps_the_legacy_alias(client, database, merged_pair):
    post_entry(client, metadata_only_payload(merged_pair))

    assert stored(database, CANONICAL_ID)["aliases"] == [
        legacy_alias(LOSER_ID, "rn2001")
    ]


@pytest.mark.parametrize("lookup_value", [LOSER_ID, "rn2001", CANONICAL_ID])
def test_merged_canonical_update_keeps_lookup_resolvable(
    lookup_value, client, bibliography, merged_pair
):
    post_entry(client, metadata_only_payload(merged_pair))

    assert bibliography.find(lookup_value)["id"] == CANONICAL_ID


def test_merged_canonical_update_keeps_the_tombstone(client, database, merged_pair):
    post_entry(client, metadata_only_payload(merged_pair))
    loser = stored(database, LOSER_ID)

    assert loser["deprecated"] is True
    assert loser["redirectTo"] == CANONICAL_ID


def test_merged_canonical_update_claims_no_reservations(client, database, merged_pair):
    post_entry(client, metadata_only_payload(merged_pair))

    assert reservations(database) == {}


def test_alias_only_canonical_metadata_update_succeeds(
    client, database, alias_only_canonical
):
    result = post_entry(client, metadata_only_payload(alias_only_canonical))

    assert result.status == falcon.HTTP_NO_CONTENT
    assert stored(database, CANONICAL_ID)["title"] == CORRECTED_TITLE


@pytest.mark.parametrize("lookup_value", [MISSING_LOSER_ID, "rn9999"])
def test_alias_only_canonical_keeps_alias_resolvable(
    lookup_value, client, bibliography, alias_only_canonical
):
    post_entry(client, metadata_only_payload(alias_only_canonical))

    assert bibliography.find(lookup_value)["id"] == CANONICAL_ID


def test_alias_shadowing_an_active_record_does_not_block_metadata_update(
    client, database
):
    canonical = seed(
        database, CANONICAL_ID, aliases=[legacy_alias("SHADOWED", "shadowed")]
    )
    seed(database, "SHADOWED")

    result = post_entry(client, metadata_only_payload(canonical))

    assert result.status == falcon.HTTP_NO_CONTENT
    assert stored(database, CANONICAL_ID)["title"] == CORRECTED_TITLE


def test_ambiguous_alias_does_not_block_metadata_update(client, database):
    canonical = seed(database, CANONICAL_ID, aliases=[legacy_alias("SHARED", "shared")])
    seed(database, "Q30000077", aliases=[legacy_alias("SHARED", "shared")])

    result = post_entry(client, metadata_only_payload(canonical))

    assert result.status == falcon.HTTP_NO_CONTENT
    assert stored(database, CANONICAL_ID)["title"] == CORRECTED_TITLE


def test_duplicate_citation_key_does_not_block_metadata_update(client, database):
    canonical = seed(database, CANONICAL_ID, citationKey="shared1967Key")
    seed(database, "Q30000078", citationKey="shared1967Key")

    result = post_entry(client, metadata_only_payload(canonical))

    assert result.status == falcon.HTTP_NO_CONTENT
    assert stored(database, CANONICAL_ID)["title"] == CORRECTED_TITLE
