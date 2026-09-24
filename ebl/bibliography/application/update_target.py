from typing import Callable

from ebl.errors import DataError, DuplicateError, NotFoundError


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
        raise DuplicateError(
            f"Bibliography entry {id_} is deprecated; "
            f"reload the entry and edit {stored_entry.get('redirectTo')} instead."
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
