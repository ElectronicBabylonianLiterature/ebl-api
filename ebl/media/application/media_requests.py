from enum import Enum
from types import MappingProxyType
from typing import Mapping, Optional, Sequence

import attr

from ebl.media.domain.validation import not_blank, tuple_or_empty
from ebl.transliteration.domain.museum_number import MuseumNumber


class ImportMode(Enum):
    """What an import does with a source that already has a media record."""

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
