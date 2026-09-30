from typing import Callable

from ebl.errors import DuplicateError, NotFoundError

MAX_REDIRECT_DEPTH = 5


def follow_bibliography_redirect(
    entry: dict, query_by_id: Callable[[str], dict]
) -> dict:
    current = entry
    visited_ids: set[str] = set()
    redirects_followed = 0

    while current.get("deprecated", False):
        current_id = current.get("id")
        redirect_to = current.get("redirectTo")
        if not isinstance(redirect_to, str) or not redirect_to:
            raise NotFoundError(
                f"Deprecated bibliography {current_id} has no redirect target."
            )
        if current_id in visited_ids or redirect_to in visited_ids:
            raise DuplicateError(
                f"Bibliography redirect loop detected at {current_id}."
            )
        if redirects_followed >= MAX_REDIRECT_DEPTH:
            raise DuplicateError(
                f"Bibliography redirect from {entry.get('id')} exceeds "
                f"the maximum depth of {MAX_REDIRECT_DEPTH}."
            )

        if isinstance(current_id, str):
            visited_ids.add(current_id)
        try:
            current = query_by_id(redirect_to)
        except NotFoundError as error:
            raise NotFoundError(
                f"Bibliography redirect target {redirect_to} not found."
            ) from error
        redirects_followed += 1

    return current
