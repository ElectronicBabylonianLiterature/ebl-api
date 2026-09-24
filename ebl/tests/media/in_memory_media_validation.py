from typing import Mapping, Sequence

from ebl.media.application import MediaAlreadyExistsError, StoredMedia
from ebl.media.domain import MediaId, MediaImportSource


def require_unique_import_sources(
    current: Mapping[MediaId, StoredMedia], replacements: Sequence[StoredMedia]
) -> None:
    resulting = dict(current)
    resulting.update((item.media.id, item) for item in replacements)
    owners_by_source: dict[MediaImportSource, MediaId] = {}
    for item in resulting.values():
        source = item.media.import_source
        if source is None:
            continue
        if source in owners_by_source:
            raise MediaAlreadyExistsError(item.media.id)
        owners_by_source[source] = item.media.id
