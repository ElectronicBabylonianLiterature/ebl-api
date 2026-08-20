"""Applying trusted identity commands to a stored bibliography entry.

Every function here is pure: it turns a stored entry plus a validated command
payload into the intended new entry. Nothing is claimed, persisted or logged,
so the result can be validated before any write happens.
"""

from copy import deepcopy
from typing import Any, Mapping, MutableMapping, Sequence

from ebl.errors import DataError

Alias = Mapping[str, Any]


def apply_identity_commands(
    stored_entry: Mapping[str, Any], commands: Mapping[str, Any]
) -> dict[str, Any]:
    entry = deepcopy(dict(stored_entry))
    _apply_aliases(entry, commands)
    _apply_citation_key(entry, commands)
    _apply_deprecation(entry, commands)
    return entry


def _apply_aliases(
    entry: MutableMapping[str, Any], commands: Mapping[str, Any]
) -> None:
    if "removeAliases" not in commands and "addAliases" not in commands:
        return

    aliases = list(entry.get("aliases", []))
    for value in commands.get("removeAliases", []):
        aliases = _without_alias(aliases, value, entry["id"])
    for alias in commands.get("addAliases", []):
        aliases = _with_alias(aliases, alias, entry["id"])
    entry["aliases"] = aliases


def _without_alias(
    aliases: Sequence[Alias], value: str, id_: str
) -> list[dict[str, Any]]:
    remaining = [alias for alias in aliases if alias.get("value") != value]
    if len(remaining) == len(aliases):
        raise DataError(f"Bibliography entry {id_} has no alias {value}.")
    return [dict(alias) for alias in remaining]


def _with_alias(
    aliases: Sequence[Alias], alias: Alias, id_: str
) -> list[dict[str, Any]]:
    value = alias["value"]
    if any(existing.get("value") == value for existing in aliases):
        raise DataError(f"Bibliography entry {id_} already has alias {value}.")
    return [*(dict(existing) for existing in aliases), dict(alias)]


def _apply_citation_key(
    entry: MutableMapping[str, Any], commands: Mapping[str, Any]
) -> None:
    if "citationKey" not in commands:
        return

    citation_key = commands["citationKey"]
    if citation_key is None:
        entry.pop("citationKey", None)
    else:
        entry["citationKey"] = citation_key


def _apply_deprecation(
    entry: MutableMapping[str, Any], commands: Mapping[str, Any]
) -> None:
    if commands.get("reactivate"):
        entry.pop("deprecated", None)
        entry.pop("redirectTo", None)
    elif "deprecateTo" in commands:
        entry["deprecated"] = True
        entry["redirectTo"] = commands["deprecateTo"]
