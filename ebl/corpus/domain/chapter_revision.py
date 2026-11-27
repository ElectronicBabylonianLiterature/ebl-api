from typing import Optional

from ebl.corpus.domain.chapter import ChapterId
from ebl.errors import ConflictError

LEGACY_REVISION = "legacy"


def chapter_revision_conflict(
    id_: ChapterId, expected: str, actual: str
) -> ConflictError:
    return ConflictError(
        f"Chapter {id_} has changed: expected revision {expected}, found {actual}."
    )


def require_revision(id_: ChapterId, expected: Optional[str], actual: str) -> None:
    if expected is not None and expected != actual:
        raise chapter_revision_conflict(id_, expected, actual)
