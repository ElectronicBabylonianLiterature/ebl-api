from __future__ import annotations

from contextlib import contextmanager
import fcntl
import hashlib
import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile, TemporaryDirectory
from typing import Iterator, TypedDict

from ebl.fragmentarium.application.map_json import load_strict_json


class ArtifactManifest(TypedDict):
    schemaVersion: int
    sourceRevision: str
    files: dict[str, str]


def artifact_manifest_name(prefix: str) -> str:
    return f"{prefix}_artifact_manifest.json"


@contextmanager
def artifact_directory_lock(directory: Path, exclusive: bool) -> Iterator[None]:
    descriptor = os.open(directory, os.O_RDONLY)
    try:
        operation = fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH
        fcntl.flock(descriptor, operation)
        yield
    finally:
        fcntl.flock(descriptor, fcntl.LOCK_UN)
        os.close(descriptor)


def publish_artifact_set(
    output_dir: Path,
    prefix: str,
    source_revision: str,
    contents: dict[str, str],
) -> None:
    revision = source_revision.strip()
    if not revision:
        raise ValueError("sourceRevision must not be blank.")
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_name = artifact_manifest_name(prefix)
    if manifest_name in contents:
        raise ValueError("Artifact contents must not provide their own manifest.")

    with artifact_directory_lock(output_dir, exclusive=True):
        with TemporaryDirectory(prefix=f".{prefix}-artifacts-", dir=output_dir) as raw:
            staging_dir = Path(raw)
            _write_and_validate_staging(staging_dir, contents)
            manifest = _build_manifest(revision, contents)
            (staging_dir / manifest_name).write_text(manifest, encoding="utf-8")
            targets = [output_dir / name for name in contents]
            targets.append(output_dir / manifest_name)
            previous = {
                target: target.read_bytes() if target.exists() else None
                for target in targets
            }
            try:
                for target in targets:
                    os.replace(staging_dir / target.name, target)
            except Exception:
                _restore_targets(previous)
                raise


def read_validated_artifact(data_dir: Path, prefix: str, filename: str) -> str:
    if not data_dir.is_dir():
        raise FileNotFoundError(f"Map artifact directory does not exist: {data_dir}")
    with artifact_directory_lock(data_dir, exclusive=False):
        manifest_path = data_dir / artifact_manifest_name(prefix)
        if not manifest_path.is_file():
            raise FileNotFoundError(
                f"Map artifact manifest does not exist: {manifest_path}"
            )
        manifest = _validate_manifest(
            load_strict_json(
                manifest_path.read_text(encoding="utf-8"), str(manifest_path)
            ),
            data_dir,
        )
        target = data_dir / filename
        if filename not in manifest["files"]:
            raise ValueError(f"Artifact manifest does not declare {filename}.")
        return target.read_text(encoding="utf-8")


def _write_and_validate_staging(staging_dir: Path, contents: dict[str, str]) -> None:
    if not contents:
        raise ValueError("Artifact publication requires at least one file.")
    for name, content in contents.items():
        if Path(name).name != name:
            raise ValueError(f"Artifact filename must be a basename: {name!r}")
        path = staging_dir / name
        path.write_text(content, encoding="utf-8")
        if path.suffix == ".json":
            load_strict_json(path.read_text(encoding="utf-8"), str(path))


def _build_manifest(source_revision: str, contents: dict[str, str]) -> str:
    files = {
        name: hashlib.sha256(content.encode("utf-8")).hexdigest()
        for name, content in sorted(contents.items())
    }
    payload = {"schemaVersion": 1, "sourceRevision": source_revision, "files": files}
    return json.dumps(payload, indent=2, ensure_ascii=False) + "\n"


def _validate_manifest(manifest: object, data_dir: Path) -> ArtifactManifest:
    if not isinstance(manifest, dict):
        raise ValueError("Map artifact manifest must be a JSON object.")
    if manifest.get("schemaVersion") != 1:
        raise ValueError("Unsupported map artifact manifest schemaVersion.")
    revision = manifest.get("sourceRevision")
    files = manifest.get("files")
    if not isinstance(revision, str) or not revision.strip():
        raise ValueError("Map artifact manifest sourceRevision must not be blank.")
    if not isinstance(files, dict) or not files:
        raise ValueError("Map artifact manifest files must be a nonempty object.")
    validated_files: dict[str, str] = {}
    for name, expected in files.items():
        if not isinstance(name, str) or Path(name).name != name:
            raise ValueError("Map artifact manifest contains an invalid filename.")
        if not isinstance(expected, str):
            raise ValueError(f"Map artifact checksum for {name} must be a string.")
        path = data_dir / name
        if not path.is_file():
            raise FileNotFoundError(f"Declared map artifact does not exist: {path}")
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != expected:
            raise ValueError(f"Map artifact checksum mismatch for {name}.")
        validated_files[name] = expected
    return {
        "schemaVersion": 1,
        "sourceRevision": revision,
        "files": validated_files,
    }


def _restore_targets(previous: dict[Path, bytes | None]) -> None:
    for target, content in previous.items():
        if content is None:
            target.unlink(missing_ok=True)
            continue
        with NamedTemporaryFile(dir=target.parent, delete=False) as temporary:
            temporary.write(content)
            restore_path = Path(temporary.name)
        os.replace(restore_path, target)
