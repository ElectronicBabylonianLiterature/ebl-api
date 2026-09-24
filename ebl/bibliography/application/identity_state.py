from copy import deepcopy
from typing import Any, Mapping, MutableMapping, Sequence

from ebl.bibliography.application.partner_identity import normalize_partner_id
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
    if not value.strip():
        raise DataError("Bibliography aliases must not be blank.")
    if any(existing.get("value") == value for existing in aliases):
        raise DataError(f"Bibliography entry {id_} already has alias {value}.")
    normalized_value = normalize_partner_id(value)
    if not normalized_value:
        raise DataError(
            "Bibliography aliases must contain at least one letter or digit."
        )
    submitted_normalized_value = alias.get("normalizedValue")
    if submitted_normalized_value not in (None, normalized_value):
        raise DataError(
            f"Bibliography alias {value} has an inconsistent normalized value."
        )
    normalized_alias = {**alias, "normalizedValue": normalized_value}
    return [*(dict(existing) for existing in aliases), normalized_alias]


def _apply_citation_key(
    entry: MutableMapping[str, Any], commands: Mapping[str, Any]
) -> None:
    if "citationKey" not in commands:
        return

    citation_key = commands["citationKey"]
    if citation_key is None:
        entry.pop("citationKey", None)
    else:
        if not citation_key.strip():
            raise DataError("Bibliography citation keys must not be blank.")
        entry["citationKey"] = citation_key


def _apply_deprecation(
    entry: MutableMapping[str, Any], commands: Mapping[str, Any]
) -> None:
    if commands.get("reactivate"):
        entry.pop("deprecated", None)
        entry.pop("redirectTo", None)
    elif "deprecateTo" in commands:
        if not commands["deprecateTo"].strip():
            raise DataError("Bibliography redirect targets must not be blank.")
        entry["deprecated"] = True
        entry["redirectTo"] = commands["deprecateTo"]
