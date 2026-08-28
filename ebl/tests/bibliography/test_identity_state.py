import pytest

from ebl.bibliography.application.identity_state import apply_identity_commands
from ebl.errors import DataError

BASE = {"id": "Q1", "type": "book", "title": "Title"}


def alias(value: str, **overrides) -> dict:
    return {"value": value, **overrides}


def test_no_commands_returns_an_equal_entry():
    assert apply_identity_commands(BASE, {}) == BASE


def test_the_stored_entry_is_not_mutated():
    stored = {**BASE, "aliases": [alias("a")]}

    apply_identity_commands(stored, {"addAliases": [alias("b")]})

    assert stored["aliases"] == [alias("a")]


def test_add_alias_to_an_entry_without_aliases():
    assert apply_identity_commands(BASE, {"addAliases": [alias("a")]})["aliases"] == [
        alias("a")
    ]


def test_add_alias_appends_after_existing_ones():
    stored = {**BASE, "aliases": [alias("a")]}

    result = apply_identity_commands(stored, {"addAliases": [alias("b")]})

    assert result["aliases"] == [alias("a"), alias("b")]


def test_removals_are_applied_before_additions():
    stored = {**BASE, "aliases": [alias("a")]}

    result = apply_identity_commands(
        stored, {"removeAliases": ["a"], "addAliases": [alias("a", type="fixed")]}
    )

    assert result["aliases"] == [alias("a", type="fixed")]


def test_removing_the_last_alias_leaves_an_empty_list():
    stored = {**BASE, "aliases": [alias("a")]}

    assert apply_identity_commands(stored, {"removeAliases": ["a"]})["aliases"] == []


def test_removing_an_absent_alias_raises():
    with pytest.raises(DataError, match="has no alias a"):
        apply_identity_commands(BASE, {"removeAliases": ["a"]})


def test_adding_an_existing_alias_raises():
    stored = {**BASE, "aliases": [alias("a")]}

    with pytest.raises(DataError, match="already has alias a"):
        apply_identity_commands(stored, {"addAliases": [alias("a")]})


def test_alias_key_is_absent_when_no_alias_command_is_given():
    assert "aliases" not in apply_identity_commands(BASE, {"citationKey": "k"})


def test_set_citation_key():
    assert apply_identity_commands(BASE, {"citationKey": "k"})["citationKey"] == "k"


def test_remove_citation_key():
    stored = {**BASE, "citationKey": "k"}

    assert "citationKey" not in apply_identity_commands(stored, {"citationKey": None})


def test_remove_an_absent_citation_key_is_tolerated():
    assert "citationKey" not in apply_identity_commands(BASE, {"citationKey": None})


def test_deprecate_to_sets_both_fields():
    result = apply_identity_commands(BASE, {"deprecateTo": "Q2"})

    assert result["deprecated"] is True
    assert result["redirectTo"] == "Q2"


def test_reactivate_clears_both_fields():
    stored = {**BASE, "deprecated": True, "redirectTo": "Q2"}

    result = apply_identity_commands(stored, {"reactivate": True})

    assert "deprecated" not in result
    assert "redirectTo" not in result


def test_reactivate_on_an_active_entry_changes_nothing():
    assert apply_identity_commands(BASE, {"reactivate": True}) == BASE


def test_commands_combine():
    stored = {**BASE, "aliases": [alias("a")], "citationKey": "old"}

    result = apply_identity_commands(
        stored,
        {
            "removeAliases": ["a"],
            "addAliases": [alias("b")],
            "citationKey": "new",
            "deprecateTo": "Q2",
        },
    )

    assert result["aliases"] == [alias("b")]
    assert result["citationKey"] == "new"
    assert result["redirectTo"] == "Q2"
