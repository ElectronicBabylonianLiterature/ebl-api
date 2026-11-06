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
    if document.get("kind") != "photo" or not isinstance(document.get("outcome"), str):
        raise ValueError("Journal result lacks a valid kind or outcome.")


class BackfillJournal:
    def __init__(self, path: Path, header: Mapping, resume: bool) -> None:
        self.path = path
        self.header = dict(header, kind="header", schema=2)
        self.file: BinaryIO = path.open("r+b" if resume else "x+b")
        self.last_source: str | None = None
        self.completed = False
        self.counts: Counter[str] = Counter()
        self.pending: dict[str, list[dict]] = {}
        self.digest = hashlib.sha256()
        self.staging: BackfillStagingJournal | None = None
        try:
            fcntl.flock(self.file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            if resume:
                self._recover()
            else:
                self._write(self.header)
            if header.get("command") == "apply":
                staging_path = path.with_name(path.name + ".staging.jsonl")
                staging_resume = resume and (
                    staging_path.exists()
                    or self.last_source is not None
                    or self.completed
                )
                self.staging = BackfillStagingJournal(
                    staging_path,
                    dict(header, command="apply-staging"),
                    staging_resume,
                )
                self.pending = self.staging.pending
                if self.completed and not self.staging.completed:
                    raise ValueError(
                        "Completed apply lacks a completed staging journal."
                    )
        except BaseException:
            if self.staging is not None:
                self.staging.__exit__()
            self.file.close()
            raise

    def __enter__(self) -> "BackfillJournal":
        return self

    def __exit__(self, *_arguments: object) -> None:
        if self.staging is not None:
            self.staging.__exit__()
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
                self._validate(document)
                self._remember(document)
                self.digest.update(line)

    def _remember(self, document: Mapping) -> None:
        source_id = document["sourceId"]
        self.last_source = source_id
        self.counts[document["outcome"]] += 1

    def _validate(self, document: Mapping) -> None:
        validate_entry(document)

    def _write(self, document: Mapping) -> None:
        line = json_bytes(document)
        self.file.write(line)
        self.file.flush()
        os.fsync(self.file.fileno())
        self.digest.update(line)

    def append(self, document: Mapping) -> None:
        if self.completed:
            raise ValueError("A completed journal cannot be extended.")
        self._validate(document)
        self._write(document)
        self._remember(document)

    def stage(self, source_id: str, handle: Mapping) -> None:
        if self.completed or self.staging is None:
            raise ValueError("Staging requires an incomplete apply journal.")
        self.staging.append(
            {
                "sourceId": source_id,
                "handles": [*self.pending.get(source_id, []), dict(handle)],
            }
        )

    def reconcile(self, source_id: str) -> None:
        if self.completed or self.staging is None:
            raise ValueError("Reconciliation requires an incomplete apply journal.")
        self.staging.append({"sourceId": source_id, "handles": []})

    def finish(self) -> None:
        if not self.completed:
            if self.staging is not None:
                self.staging.finish()
            self._write(
                {
                    "kind": "complete",
                    "sha256": self.digest.hexdigest(),
                    "counts": dict(self.counts),
                    "pendingSources": sorted(self.pending),
                }
            )
            self.completed = True


class BackfillStagingJournal(BackfillJournal):
    def _validate(self, document: Mapping) -> None:
        if set(document) != {"sourceId", "handles"} or not isinstance(
            document["sourceId"], str
        ):
            raise ValueError("Staging rows require a source identity and handle array.")
        handles = document["handles"]
        if not isinstance(handles, list) or not all(
            isinstance(handle, dict) for handle in handles
        ):
            raise ValueError("Staging handles must be objects.")

    def _remember(self, document: Mapping) -> None:
        source_id = document["sourceId"]
        if document["handles"]:
            self.pending[source_id] = document["handles"]
        else:
            self.pending.pop(source_id, None)
