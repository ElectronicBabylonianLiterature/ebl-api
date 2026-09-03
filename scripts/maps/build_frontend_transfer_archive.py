#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tarfile

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from ebl.fragmentarium.application.map_artifact_generator import (  # noqa: E402
    DEFAULT_OUTPUT_DIR,
)
from ebl.fragmentarium.application.map_site_config import (  # noqa: E402
    CRS_EPSG,
    SITE_CONFIGS,
)
from ebl.fragmentarium.application.map_geometry import CANONICAL_CRS  # noqa: E402

GENERATOR_VERSION = "map_artifact_generator/2"


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], capture_output=True, text=True, check=True
    ).stdout.strip()


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _site_summary(data_dir: Path, site_id: str) -> dict:
    config = SITE_CONFIGS[site_id]
    prefix = site_id.lower()
    inventory = json.loads(
        (data_dir / f"{prefix}_polygon_inventory.json").read_text(encoding="utf-8")
    )
    mappings = json.loads(
        (data_dir / f"{prefix}_findspot_polygon_mappings.json").read_text(
            encoding="utf-8"
        )
    )
    curation = json.loads(
        (data_dir / f"{prefix}_findspot_polygon_curation_template.json").read_text(
            encoding="utf-8"
        )
    )
    distinct_polygons = {
        polygon_id for mapping in mappings for polygon_id in mapping["polygonIds"]
    }
    source_revisions = sorted({mapping["sourceRevision"] for mapping in mappings})
    return {
        "siteId": site_id,
        "siteName": config.site_name,
        "authoritativeSource": config.source_label,
        "sourceCrs": CRS_EPSG[config.crs_kind],
        "sourceRevisions": source_revisions,
        "polygonCount": len(inventory),
        "mappingCount": len(mappings),
        "distinctMappedPolygonCount": len(distinct_polygons),
        "unresolvedCount": len(curation),
    }


def build_manifest(data_dir: Path, included_files: list[Path]) -> str:
    lines = [
        "eBL Interactive Map — Multi-Site Frontend Transfer Manifest",
        "",
        "repository: ElectronicBabylonianLiterature/ebl-api",
        f"branch: {_git('rev-parse', '--abbrev-ref', 'HEAD')}",
        f"commit: {_git('rev-parse', 'HEAD')}",
        f"targetCanonicalCrs: {CANONICAL_CRS}",
        f"generatorVersion: {GENERATOR_VERSION}",
        "",
        "Per-site summary:",
    ]
    for site_id in SITE_CONFIGS:
        summary = _site_summary(data_dir, site_id)
        lines.append(f"- {site_id} ({summary['siteName']})")
        for key, value in summary.items():
            if key in {"siteId", "siteName"}:
                continue
            lines.append(f"    {key}: {value}")
    lines.append("")
    lines.append("File checksums (SHA-256):")
    for path in included_files:
        lines.append(f"- {path.name}: {_sha256(path)}")
    lines.append("")
    return "\n".join(lines) + "\n"


def build_archive(data_dir: Path, output_path: Path) -> Path:
    included_files = [
        data_dir / f"{site_id.lower()}_{suffix}"
        for site_id in SITE_CONFIGS
        for suffix in ("polygon_inventory.json", "findspot_polygon_mappings.json")
    ]
    missing = [path for path in included_files if not path.exists()]
    if missing:
        raise FileNotFoundError(f"Missing generated artifacts: {missing}")

    manifest = build_manifest(data_dir, included_files)
    manifest_path = data_dir / "ARTIFACT_MANIFEST.txt"
    manifest_path.write_text(manifest, encoding="utf-8")

    with tarfile.open(output_path, "w:gz") as archive:
        archive.add(manifest_path, arcname="ARTIFACT_MANIFEST.txt")
        for path in included_files:
            archive.add(path, arcname=path.name)
    manifest_path.unlink()
    return output_path


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build the multi-site frontend-transfer archive"
    )
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("map-multi-site-canonical-artifacts.tar.gz"),
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    output_path = build_archive(args.data_dir, args.output)
    print(f"Wrote {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
