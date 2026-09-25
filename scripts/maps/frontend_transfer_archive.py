from __future__ import annotations

import gzip
import hashlib
from io import BytesIO
import json
from pathlib import Path
import subprocess
import tarfile
from tempfile import NamedTemporaryFile
from typing import BinaryIO, cast

from ebl.fragmentarium.application.map_geometry import CANONICAL_CRS
from ebl.fragmentarium.application.map_site_config import SITE_CONFIGS
from scripts.maps.frontend_transfer_validation import read_artifact_sets, site_summary

ARCHIVE_MANIFEST = "ARTIFACT_MANIFEST.txt"
GENERATOR_VERSION = "map_artifact_generator/2"
FRONTEND_GEOMETRY_COMMIT = "b8188ac7026ab96687c1f42f09ee1d154d80cd64"
FRONTEND_GENERATOR_COMMIT = "894a764fbd06fc5e6b671bc94c40da105c3d6fa5"
FRONTEND_GENERATOR_PATH = "scripts/maps/build-findspot-map-assets.py"
FRONTEND_GENERATOR_EXPECTATIONS = {
    "assur": {"features": 134, "inventory": 134, "mappings": 315, "mapped": 133},
    "kalhu": {"features": 12, "inventory": 12, "mappings": 7, "mapped": 7},
    "nippur": {"features": 20, "inventory": 20, "mappings": 18, "mapped": 9},
    "uruk": {"features": 128, "inventory": 128, "mappings": 129, "mapped": 125},
}
TRANSFER_SUFFIXES = ("polygon_inventory.json", "findspot_polygon_mappings.json")


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


def _transfer_names() -> tuple[str, ...]:
    return tuple(
        f"{site_id.lower()}_{suffix}"
        for site_id in SITE_CONFIGS
        for suffix in TRANSFER_SUFFIXES
    )


def build_manifest(contents: dict[str, bytes], revisions: dict[str, str]) -> bytes:
    dirty = bool(_git("status", "--porcelain", "--untracked-files=normal"))
    lines = [
        "eBL Interactive Map — Multi-Site Frontend Transfer Manifest",
        "",
        "repository: ElectronicBabylonianLiterature/ebl-api",
        f"commit: {_git('rev-parse', 'HEAD')}",
        f"dirtyWorktree: {str(dirty).lower()}",
        f"targetCanonicalCrs: {CANONICAL_CRS}",
        f"generatorVersion: {GENERATOR_VERSION}",
        "geometryIncluded: false",
        "geometryRequiredFiles: assur.geojson, kalhu.geojson, nippur.geojson, uruk.geojson",
        "geometryRepository: ElectronicBabylonianLiterature/ebl-frontend",
        f"geometryCommit: {FRONTEND_GEOMETRY_COMMIT}",
        "geometryJoin: polygonId and geometryChecksum",
        "frontendGeneratorRepository: ElectronicBabylonianLiterature/ebl-frontend",
        f"frontendGeneratorCommit: {FRONTEND_GENERATOR_COMMIT}",
        f"frontendGeneratorPath: {FRONTEND_GENERATOR_PATH}",
        "frontendGeneratorArchiveStep: extract this archive into <artifact-dir>",
        "frontendGeneratorExpectationsJson: "
        + json.dumps(FRONTEND_GENERATOR_EXPECTATIONS, separators=(",", ":")),
        (
            "frontendGeneratorCommand: python3 "
            f"{FRONTEND_GENERATOR_PATH} --findspot-dir <geojson-dir> "
            "--artifact-dir <artifact-dir> --expectations <updated-counts.json>"
        ),
        "",
        "Per-site summary:",
    ]
    all_findspot_ids: set[int] = set()
    for site_id in SITE_CONFIGS:
        summary, findspot_ids = site_summary(contents, revisions, site_id)
        if all_findspot_ids & findspot_ids:
            raise ValueError("Findspot IDs must be unique across sites")
        all_findspot_ids.update(findspot_ids)
        lines.append(f"- {site_id} ({summary['siteName']})")
        lines.extend(
            f"    {key}: {value}"
            for key, value in summary.items()
            if key not in {"siteId", "siteName"}
        )
    lines.extend(("", "File checksums (SHA-256):"))
    lines.extend(f"- {name}: {_sha256(contents[name])}" for name in _transfer_names())
    return ("\n".join((*lines, "")) + "\n").encode("utf-8")


def _add_member(archive: tarfile.TarFile, name: str, content: bytes) -> None:
    if not name or Path(name).name != name:
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
    members = ((ARCHIVE_MANIFEST, build_manifest(contents, revisions)),) + tuple(
        (name, contents[name]) for name in _transfer_names()
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
