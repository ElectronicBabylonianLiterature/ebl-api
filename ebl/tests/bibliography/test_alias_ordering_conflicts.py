"""Alias order is not identity.

No production code reads an alias by position: lookup values are collected into
a set, and Mongo matches `aliases.normalizedValue` against the array as a whole.
An editor that re-serialises the list in another order has therefore changed
nothing, and must not be told to reload. Anything that changes the multiset --
an alias added, removed, duplicated or edited -- is still a conflict, and the
stored order is never rewritten by a submission.
"""

import falcon
import pytest

from ebl.bibliography.application.server_owned_fields import (
    canonical_aliases,
    changed_server_owned_fields,
)
from ebl.tests.bibliography.identity_preservation_test_helpers import (
    CORRECTED_TITLE,
    post_entry,
)
from ebl.tests.factories.bibliography import BibliographyEntryFactory

ALIAS_A = {
    "value": "RN9001",
    "normalizedValue": "rn9001",
    "type": "legacy_id",
    "source": "duplicate_merge_2026-08-04",
    "status": "redirect",
}
ALIAS_B = {"value": "RN9002", "normalizedValue": "rn9002"}
ALIAS_C = {"value": "RN9003", "normalizedValue": "rn9003"}
STORED_ORDER = [ALIAS_A, ALIAS_B]
EDITED_ALIAS_A = {**ALIAS_A, "status": "active"}


@pytest.fixture
def multi_alias_entry(bibliography, user):
    entry = BibliographyEntryFactory.build(
        id="Q30000501", title="Original", aliases=list(STORED_ORDER)
    )
    bibliography.create(entry, user)
    return entry


def submission(entry: dict, aliases: list) -> dict:
    return {**entry, "title": CORRECTED_TITLE, "aliases": aliases}


@pytest.mark.parametrize(
    "aliases", [STORED_ORDER, list(reversed(STORED_ORDER))], ids=["same", "reversed"]
)
def test_the_same_aliases_in_any_order_are_accepted(
    aliases, client, bibliography, multi_alias_entry
):
    result = post_entry(client, submission(multi_alias_entry, list(aliases)))

    assert result.status == falcon.HTTP_NO_CONTENT
    assert bibliography.find(multi_alias_entry["id"])["title"] == CORRECTED_TITLE


def test_a_reordered_submission_does_not_rewrite_the_stored_order(
    client, bibliography, multi_alias_entry
):
    post_entry(client, submission(multi_alias_entry, list(reversed(STORED_ORDER))))

    assert bibliography.find(multi_alias_entry["id"])["aliases"] == STORED_ORDER


@pytest.mark.parametrize(
    "aliases",
    [
        [*STORED_ORDER, ALIAS_C],
        [ALIAS_A],
        [EDITED_ALIAS_A, ALIAS_B],
        [ALIAS_A, ALIAS_A],
    ],
    ids=["added", "removed", "edited", "duplicated"],
)
def test_a_changed_alias_multiset_is_still_a_conflict(
    aliases, client, bibliography, multi_alias_entry
):
    result = post_entry(client, submission(multi_alias_entry, list(aliases)))

    assert result.status == falcon.HTTP_CONFLICT
    assert "aliases" in result.text
    assert bibliography.find(multi_alias_entry["id"])["aliases"] == STORED_ORDER


def test_canonical_aliases_is_order_insensitive_but_keeps_duplicates():
    assert canonical_aliases(STORED_ORDER) == canonical_aliases(
        list(reversed(STORED_ORDER))
    )
    assert canonical_aliases([ALIAS_A, ALIAS_A]) != canonical_aliases([ALIAS_A])


def test_changed_server_owned_fields_ignores_alias_order_only():
    stored_entry = {"aliases": STORED_ORDER, "citationKey": "dossin1967La"}

    assert (
        changed_server_owned_fields(
            {"aliases": list(reversed(STORED_ORDER))}, stored_entry
        )
        == []
    )
    assert changed_server_owned_fields({"aliases": [ALIAS_A]}, stored_entry) == [
        "aliases"
    ]
    assert changed_server_owned_fields({"citationKey": "other"}, stored_entry) == [
        "citationKey"
    ]


@pytest.mark.parametrize("value", [None, [], "not-a-list"])
def test_a_non_list_alias_value_is_compared_unchanged(value):
    assert changed_server_owned_fields({"aliases": value}, {"aliases": STORED_ORDER})
