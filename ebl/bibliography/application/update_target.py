"""Choosing which stored record a metadata update is allowed to write to.

`Bibliography.find` resolves a citation key, an alias or a redirect and answers
with the canonical entry. An update deliberately does not: a write names one
exact record, because a client that edited what it believed was one entry must
never silently overwrite a different one that an identifier happened to resolve
to. Reads may follow identity, writes may not.

Both non-canonical identifiers are therefore refused, and each refusal names the
record the caller should edit instead rather than leaving them with a bare
`404`: a deprecated id points at its redirect target, and a citation key or
alias points at the entry it belongs to. An identifier that resolves to nothing
at all stays a `404`.
"""

from typing import Callable

from ebl.errors import DataError, NotFoundError


def stored_entry_for_update(
    entry: dict,
    query_by_id: Callable[[str], dict],
    find: Callable[[str], dict],
) -> dict:
    id_ = entry.get("id")
    if not isinstance(id_, str) or not id_:
        raise DataError("Bibliography entry id is required.")
    stored_entry = query_canonical_entry(id_, query_by_id, find)
    if stored_entry.get("deprecated"):
        raise DataError(
            f"Bibliography entry {id_} is deprecated; "
            f"edit {stored_entry.get('redirectTo')} instead."
        )
    return stored_entry


def query_canonical_entry(
    id_: str,
    query_by_id: Callable[[str], dict],
    find: Callable[[str], dict],
) -> dict:
    try:
        return query_by_id(id_)
    except NotFoundError as error:
        canonical_entry = find(id_)
        raise DataError(
            f"Bibliography entry {id_} cannot be edited through a citation key "
            f"or alias; edit {canonical_entry['id']} instead."
        ) from error
