from __future__ import annotations

import hashlib
from pathlib import Path

from ebl.fragmentarium.application.map_artifact_storage import (
    artifact_directory_lock,
    artifact_manifest_name,
)
from ebl.fragmentarium.application.map_json import load_strict_json
from ebl.fragmentarium.application.map_site_config import SITE_CONFIGS

ARTIFACT_SUFFIXES = (
    "polygon_inventory.json",
    "findspot_polygon_mappings.json",
    "findspot_polygon_curation_template.json",
    "findspot_polygon_curation_report.md",
)


def read_artifact_sets(data_dir: Path) -> tuple[dict[str, bytes], dict[str, str]]:
    if not data_dir.is_dir():
        raise FileNotFoundError(f"Map artifact directory does not exist: {data_dir}")
    contents: dict[str, bytes] = {}
    revisions: dict[str, str] = {}
    with artifact_directory_lock(data_dir, exclusive=False):
        for site_id in SITE_CONFIGS:
            manifest_path = data_dir / artifact_manifest_name(site_id.lower())
            revision, declared_files = _read_manifest(manifest_path, site_id)
            revisions[site_id] = revision
            contents.update(
                _read_declared_files(data_dir, declared_files, manifest_path)
            )
    return contents, revisions


def _artifact_names(site_id: str) -> set[str]:
    prefix = site_id.lower()
    return {f"{prefix}_{suffix}" for suffix in ARTIFACT_SUFFIXES}


def _regular_file(path: Path) -> Path:
    if not path.is_file() or path.is_symlink():
        raise FileNotFoundError(f"Missing regular artifact: {path}")
    return path


def _read_manifest(manifest_path: Path, site_id: str) -> tuple[str, dict[str, object]]:
    manifest = load_strict_json(
        _regular_file(manifest_path).read_text(encoding="utf-8"), str(manifest_path)
    )
    if not isinstance(manifest, dict) or manifest.get("schemaVersion") != 1:
        raise ValueError(f"Invalid artifact manifest: {manifest_path}")
    revision = manifest.get("sourceRevision")
    declared_files = manifest.get("files")
    if not isinstance(revision, str) or not revision.strip():
        raise ValueError(f"Invalid source revision in {manifest_path}")
    if not isinstance(declared_files, dict) or set(declared_files) != _artifact_names(
        site_id
    ):
        raise ValueError(
            f"Artifact manifest has unexpected declarations: {manifest_path}"
        )
    return revision, declared_files


def _read_declared_files(
    data_dir: Path, declared_files: dict[str, object], manifest_path: Path
) -> dict[str, bytes]:
    contents: dict[str, bytes] = {}
    for name in sorted(declared_files):
        expected_hash = declared_files[name]
        if not isinstance(expected_hash, str):
            raise ValueError(f"Invalid checksum for {name} in {manifest_path}")
        content = _regular_file(data_dir / name).read_bytes()
        if hashlib.sha256(content).hexdigest() != expected_hash:
            raise ValueError(f"Artifact checksum mismatch for {name}")
        contents[name] = content
    return contents
