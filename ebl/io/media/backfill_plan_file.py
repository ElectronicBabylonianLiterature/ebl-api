import hashlib
import shutil
from contextlib import contextmanager
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Iterator

from ebl.io.media.backfill_journal import read_document
from ebl.io.media.backfill_plan_validation import (
    validate_plan_header,
    validate_plan_photo,
)


def inspect_plan(path: Path) -> tuple[dict, str]:
    digest = hashlib.sha256()
    completed = False
    with path.open("rb") as stream:
        first = stream.readline()
        header = read_document(first)
        if (
            header.get("kind") != "header"
            or header.get("schema") != 1
            or header.get("command") != "dry-run"
        ):
            raise ValueError("Not a supported dry-run plan.")
        validate_plan_header(header)
        digest.update(first)
        for line in stream:
            if not line.endswith(b"\n") or completed:
                raise ValueError("Plan is incomplete or has trailing data.")
            document = read_document(line)
            if document.get("kind") == "complete":
                if document.get("sha256") != digest.hexdigest():
                    raise ValueError("Plan checksum does not match its contents.")
                completed = True
            else:
                if document.get("kind") != "photo":
                    raise ValueError("Plan contains an unknown row kind.")
                validate_plan_photo(document)
                digest.update(line)
        if not completed:
            raise ValueError("Only a completed dry-run plan can be applied.")
    return header, digest.hexdigest()


def plan_rows(path: Path, resume_after: str | None) -> Iterator[dict]:
    reached = resume_after is None
    with path.open("rb") as stream:
        next(stream)
        for line in stream:
            document = read_document(line)
            if document.get("kind") == "complete":
                break
            if reached:
                yield document
            elif document.get("sourceId") == resume_after:
                reached = True
    if not reached:
        raise ValueError("Resume source is absent from the bound plan.")


@contextmanager
def verified_plan(path: Path) -> Iterator[tuple[Path, dict, str]]:
    with path.open("rb") as source, NamedTemporaryFile(mode="w+b") as snapshot:
        shutil.copyfileobj(source, snapshot, length=1_048_576)
        snapshot.flush()
        snapshot_path = Path(snapshot.name)
        header, digest = inspect_plan(snapshot_path)
        yield snapshot_path, header, digest
