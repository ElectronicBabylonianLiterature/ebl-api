import fcntl
import hashlib
import json
import os
from collections import Counter
from pathlib import Path
from typing import BinaryIO, Mapping


def json_bytes(document: Mapping) -> bytes:
    return (json.dumps(document, sort_keys=True, separators=(",", ":")) + "\n").encode(
        "utf-8"
    )


def read_document(line: bytes) -> dict:
    document = json.loads(line)
    if not isinstance(document, dict):
        raise ValueError("Journal rows must be objects.")
    return document


def validate_entry(document: Mapping) -> None:
    if not isinstance(document.get("sourceId"), str):
        raise ValueError("Journal result lacks a source identity.")
    kind = document.get("kind")
    if kind == "staged" and isinstance(document.get("handle"), dict):
        return
    if kind == "reconciled":
        return
    if kind != "photo" or not isinstance(document.get("outcome"), str):
        raise ValueError("Journal result lacks a valid kind or outcome.")


class BackfillJournal:
    def __init__(self, path: Path, header: Mapping, resume: bool) -> None:
        self.path = path
        self.header = dict(header, kind="header", schema=1)
        self.file: BinaryIO = path.open("r+b" if resume else "x+b")
        self.last_source: str | None = None
        self.completed = False
        self.counts: Counter[str] = Counter()
        self.pending: dict[str, list[dict]] = {}
        self.digest = hashlib.sha256()
        try:
            fcntl.flock(self.file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            if resume:
                self._recover()
            else:
                self._write(self.header)
        except BaseException:
            self.file.close()
            raise

    def __enter__(self) -> "BackfillJournal":
        return self

    def __exit__(self, *_arguments: object) -> None:
        self.file.close()

    def _recover(self) -> None:
        first = self.file.readline()
        if read_document(first) != self.header:
            raise ValueError("Resume target, plan or policy differs from the journal.")
        self.digest.update(first)
        while True:
            offset = self.file.tell()
            line = self.file.readline()
            if not line:
                break
            if not line.endswith(b"\n"):
                self.file.seek(offset)
                self.file.truncate()
                self.file.flush()
                os.fsync(self.file.fileno())
                break
            document = read_document(line)
            if self.completed:
                raise ValueError("Journal has rows after its completion marker.")
            if document.get("kind") == "complete":
                if document.get("sha256") != self.digest.hexdigest():
                    raise ValueError("Journal completion checksum does not match.")
                self.completed = True
            else:
                validate_entry(document)
                self._remember(document)
                self.digest.update(line)

    def _remember(self, document: Mapping) -> None:
        source_id = document["sourceId"]
        if document.get("kind") == "staged":
            self.pending.setdefault(source_id, []).append(document["handle"])
            return
        if document.get("kind") == "reconciled":
            self.pending.pop(str(source_id), None)
            return
        self.last_source = source_id
        self.counts[document["outcome"]] += 1

    def _write(self, document: Mapping) -> None:
        line = json_bytes(document)
        self.file.write(line)
        self.file.flush()
        os.fsync(self.file.fileno())
        self.digest.update(line)

    def append(self, document: Mapping) -> None:
        if self.completed:
            raise ValueError("A completed journal cannot be extended.")
        validate_entry(document)
        self._write(document)
        self._remember(document)

    def stage(self, source_id: str, handle: Mapping) -> None:
        self.append({"kind": "staged", "sourceId": source_id, "handle": dict(handle)})

    def reconcile(self, source_id: str) -> None:
        self.append({"kind": "reconciled", "sourceId": source_id})

    def finish(self) -> None:
        if not self.completed:
            self._write(
                {
                    "kind": "complete",
                    "sha256": self.digest.hexdigest(),
                    "counts": dict(self.counts),
                    "pendingSources": sorted(self.pending),
                }
            )
            self.completed = True
