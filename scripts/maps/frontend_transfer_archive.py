from __future__ import annotations

import gzip
import hashlib
from io import BytesIO
import json
from pathlib import Path
import re
import subprocess
import tarfile
from tempfile import NamedTemporaryFile
from typing import BinaryIO, cast

from ebl.fragmentarium.application.map_geometry import CANONICAL_CRS
from ebl.fragmentarium.application.map_polygon_identity import (
    contains_control_character,
)
from scripts.maps.frontend_transfer_contract import (
    CONTRACT_MANIFEST,
    CONTRACT_VERSION,
    GENERATOR_VERSION,
    GEOMETRY_CONTRACT_VERSION,
    TransferProvenance,
    build_contract_manifest,
    expectations,
    site_summaries,
    transfer_names,
)
from scripts.maps.frontend_transfer_manifest import read_artifact_sets

ARCHIVE_MANIFEST = "ARTIFACT_MANIFEST.txt"
FRONTEND_GENERATOR_PATH = "scripts/maps/build-findspot-map-assets.py"


def _git(*args: str) -> str:
    repository_root = Path(__file__).resolve().parents[2]
    return subprocess.run(
        ["git", "-C", str(repository_root), *args],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()


def _sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _git_provenance() -> TransferProvenance:
    records = _git(
        "status", "--porcelain=v2", "--branch", "--untracked-files=normal", "-z"
    ).split("\0")
    commit = next(
        (
            record.removeprefix("# branch.oid ")
            for record in records
            if record.startswith("# branch.oid ")
        ),
        "",
    )
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise ValueError("Git status must identify a committed producer revision")
    return TransferProvenance(
        commit, any(record and not record.startswith("# ") for record in records)
    )


def build_manifest(
    contents: dict[str, bytes],
    revisions: dict[str, str],
    provenance: TransferProvenance | None = None,
) -> bytes:
    summaries = site_summaries(contents, revisions)
    provenance = provenance or _git_provenance()
    lines = [
        "eBL Interactive Map — Multi-Site Frontend Transfer Manifest",
        "",
        "repository: ElectronicBabylonianLiterature/ebl-api",
        f"commit: {provenance.commit}",
        f"dirtyWorktree: {str(provenance.dirty_worktree).lower()}",
        f"targetCanonicalCrs: {CANONICAL_CRS}",
        f"generatorVersion: {GENERATOR_VERSION}",
        "geometryIncluded: false",
        "geometryRequiredFiles: assur.geojson, kalhu.geojson, nippur.geojson, uruk.geojson",
        "geometryRepository: ElectronicBabylonianLiterature/ebl-frontend",
        f"geometryContractVersion: {GEOMETRY_CONTRACT_VERSION}",
        "geometryJoin: polygonId and geometryChecksum",
        "frontendGeneratorRepository: ElectronicBabylonianLiterature/ebl-frontend",
        f"metadataContractVersion: {CONTRACT_VERSION}",
        f"metadataContractManifest: {CONTRACT_MANIFEST}",
        f"frontendGeneratorPath: {FRONTEND_GENERATOR_PATH}",
        "frontendGeneratorArchiveStep: extract this archive into <artifact-dir>",
        "frontendGeneratorExpectationsJson: "
        + json.dumps(expectations(summaries), separators=(",", ":")),
        (
            "frontendGeneratorCommand: python3 "
            f"{FRONTEND_GENERATOR_PATH} --findspot-dir <geojson-dir> "
            "--artifact-dir <artifact-dir> --expectations <updated-counts.json>"
        ),
        "",
        "Per-site summary:",
    ]
    for site_id, summary in summaries.items():
        lines.append(f"- {site_id} ({summary['siteName']})")
        lines.extend(
            f"    {key}: {value}"
            for key, value in summary.items()
            if key not in {"siteId", "siteName"}
        )
    lines.extend(("", "File checksums (SHA-256):"))
    lines.extend(f"- {name}: {_sha256(contents[name])}" for name in transfer_names())
    return ("\n".join(lines) + "\n").encode("utf-8")


def _safe_member_name(name: str) -> bool:
    if name in ("", ".", ".."):
        return False
    if any(character in name for character in ("/", "\\", ":")):
        return False
    return not contains_control_character(name) and Path(name).name == name


def _add_member(archive: tarfile.TarFile, name: str, content: bytes) -> None:
    if not _safe_member_name(name):
        raise ValueError(f"Archive member name must be a basename: {name!r}")
    info = tarfile.TarInfo(name)
    info.size = len(content)
    info.mode = 0o644
    info.mtime = 0
    info.uid = info.gid = 0
    info.uname = info.gname = ""
    archive.addfile(info, BytesIO(content))


def _write_archive(path: Path, members: tuple[tuple[str, bytes], ...]) -> None:
    with path.open("wb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as compressed:
            with tarfile.open(
                fileobj=cast(BinaryIO, compressed),
                mode="w",
                format=tarfile.USTAR_FORMAT,
            ) as archive:
                for name, content in members:
                    _add_member(archive, name, content)


def build_archive(data_dir: Path, output_path: Path) -> Path:
    data_dir = data_dir.resolve()
    if output_path.is_symlink():
        raise ValueError("Transfer output must not be a symbolic link")
    output_path = output_path.resolve()
    if output_path == data_dir or data_dir in output_path.parents:
        raise ValueError(
            "Transfer output must be outside the source artifact directory"
        )
    contents, revisions = read_artifact_sets(data_dir)
    provenance = _git_provenance()
    members = (
        (ARCHIVE_MANIFEST, build_manifest(contents, revisions, provenance)),
        (CONTRACT_MANIFEST, build_contract_manifest(contents, revisions, provenance)),
        *((name, contents[name]) for name in transfer_names()),
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile(
        dir=output_path.parent,
        prefix=f".{output_path.name}.",
        suffix=".tmp",
        delete=False,
    ) as temporary:
        temporary_path = Path(temporary.name)
    try:
        _write_archive(temporary_path, members)
        temporary_path.replace(output_path)
    finally:
        temporary_path.unlink(missing_ok=True)
    return output_path
