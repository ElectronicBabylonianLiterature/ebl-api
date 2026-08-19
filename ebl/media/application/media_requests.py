from enum import Enum
from types import MappingProxyType
from typing import Mapping, Optional, Sequence

import attr

from ebl.media.domain.validation import not_blank, tuple_or_empty
from ebl.transliteration.domain.museum_number import MuseumNumber


class ImportMode(Enum):
    """What an import does with a source that already has a media record.

    A source object "already has a media record" when some media's
    `import_source` equals the source object's `MediaImportSource` identity —
    the whole value: `system`, `file_id` and `container` together, with
    `container` None matching only another None. Nothing else establishes
    import identity: equal `MediaChecksum` values mean duplicate *content* and
    are reported as `BackfillCategory.DUPLICATE_CHECKSUM`, never treated as the
    same source; `MediaId`, `original_filename` and museum number are likewise
    not import identity.

    `SKIP_EXISTING` leaves such a record untouched; `REPLACE` replaces it.
    Media with no `import_source` can never match, so it is never skipped or
    replaced by an import.
    """

    SKIP_EXISTING = "skip-existing"
    REPLACE = "replace"


class BackfillCategory(Enum):
    """Closed set of audit findings a backfill run reports."""

    AMBIGUOUS_FILENAME = "ambiguous-filename"
    UNKNOWN_FRAGMENT = "unknown-fragment"
    ORPHANED_ORIGINAL = "orphaned-original"
    ORPHANED_THUMBNAIL = "orphaned-thumbnail"
    MISSING_DISPLAY = "missing-display"
    MISSING_THUMBNAIL = "missing-thumbnail"
    MULTIPLE_ORIGINALS = "multiple-originals"
    DUPLICATE_CHECKSUM = "duplicate-checksum"
    UNSUPPORTED_MIME_TYPE = "unsupported-mime-type"
    HAS_PHOTO_MISMATCH = "has-photo-mismatch"
    ORPHANED_NEW_MEDIA_FILE = "orphaned-new-media-file"


def _museum_numbers_of(
    value: Optional[Sequence[MuseumNumber]],
) -> tuple[MuseumNumber, ...]:
    return tuple_or_empty(value)


def _strings_of(value: Optional[Sequence[str]]) -> tuple[str, ...]:
    return tuple_or_empty(value)


def _frozen_reports(
    value: Optional[Mapping[BackfillCategory, Sequence[str]]],
) -> Mapping[BackfillCategory, Sequence[str]]:
    return MappingProxyType(
        {category: tuple(entries) for category, entries in (value or {}).items()}
    )


@attr.s(auto_attribs=True, frozen=True)
class ImportRequest:
    """One import run. `mode` decides what happens to sources that already have
    a media record, as defined by `ImportMode`; `dry_run` is orthogonal to the
    mode, so any mode can be previewed.
    """

    mode: ImportMode = attr.ib(validator=attr.validators.instance_of(ImportMode))
    source_name: str = attr.ib(validator=not_blank)
    fragment_ids: Sequence[MuseumNumber] = attr.ib(
        factory=tuple, converter=_museum_numbers_of
    )
    dry_run: bool = attr.ib(default=False, kw_only=True)


@attr.s(auto_attribs=True, frozen=True)
class ImportReport:
    created: int = 0
    skipped: int = 0
    replaced: int = 0
    failed: int = 0
    errors: Sequence[str] = attr.ib(factory=tuple, converter=_strings_of)
    warnings: Sequence[str] = attr.ib(factory=tuple, converter=_strings_of)


@attr.s(auto_attribs=True, frozen=True)
class BackfillRequest:
    dry_run: bool = True
    batch_size: Optional[int] = None
    resume_after: Optional[str] = None


@attr.s(auto_attribs=True, frozen=True)
class BackfillReport:
    """Outcome of one backfill batch.

    `next_resume_token` is `None` when the scan finished; otherwise it is the
    opaque cursor to pass back as `BackfillRequest.resume_after` to continue
    after the last completed boundary.
    """

    scanned: int = 0
    candidates: int = 0
    created: int = 0
    replaced: int = 0
    skipped: int = 0
    failed: int = 0
    next_resume_token: Optional[str] = None
    reports: Mapping[BackfillCategory, Sequence[str]] = attr.ib(
        factory=dict, converter=_frozen_reports
    )
