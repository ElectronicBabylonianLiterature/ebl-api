from typing import cast

import pytest

from ebl.bibliography.application.bibliography_identity import (
    ensure_lookup_values_available,
)
from ebl.bibliography.application.bibliography_repository import (
    BibliographyRepository,
    LookupValueInUseError,
)
from ebl.bibliography.infrastructure.legacy_alias_lookup import MongoLegacyAliasLookup
from ebl.errors import DuplicateError, NotFoundError


class LegacyDuplicateRepository:
    def query_by_id(self, _value):
        raise NotFoundError("missing")

    def query_by_citation_key(self, _value):
        raise NotFoundError("missing")

    def query_by_alias(self, _value):
        raise NotFoundError("missing")

    def query_by_legacy_alias(self, _value):
        raise DuplicateError("ambiguous")


def test_ambiguous_legacy_alias_is_in_use():
    with pytest.raises(LookupValueInUseError):
        ensure_lookup_values_available(
            cast(BibliographyRepository, LegacyDuplicateRepository()), ["legacy"]
        )


def test_query_rejects_an_ambiguous_legacy_alias(database):
    database["bibliography"].insert_many(
        [
            {"_id": "A", "type": "book", "aliases": [{"value": "Legacy Alias"}]},
            {"_id": "B", "type": "book", "aliases": [{"value": "legacy-alias"}]},
        ]
    )

    with pytest.raises(DuplicateError, match="ambiguous"):
        MongoLegacyAliasLookup(database).query("legacy alias")


def test_legacy_alias_matching_rejects_noncanonical_shapes():
    lookup = MongoLegacyAliasLookup

    assert lookup._matches({}, "") is False
    assert lookup._alias_matches("legacy", "legacy") is False
    assert (
        lookup._alias_matches({"value": "legacy", "normalizedValue": "x"}, "legacy")
        is False
    )
    assert lookup._alias_matches({"value": 7}, "legacy") is False
    assert lookup._alias_matches({"value": "Legacy Alias"}, "legacy-alias") is True
