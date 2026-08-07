from __future__ import annotations

from pathlib import Path

from ebl.fragmentarium.application.assur_map_sources import AssurOdsRow, AssurPolygon
from ebl.fragmentarium.application.map_artifact_generator import (
    DEFAULT_OUTPUT_DIR as _DEFAULT_OUTPUT_DIR,
    SiteArtifacts as AssurArtifacts,
    build_site_artifacts,
    write_site_artifacts,
)
from ebl.fragmentarium.application.map_site_config import SITE_CONFIGS

DEFAULT_OUTPUT_DIR = _DEFAULT_OUTPUT_DIR
_ASSUR_CONFIG = SITE_CONFIGS["ASSUR"]

__all__ = [
    "DEFAULT_OUTPUT_DIR",
    "AssurArtifacts",
    "build_assur_artifacts",
    "write_assur_artifacts",
]


def build_assur_artifacts(
    source_revision: str,
    ods_rows: tuple[AssurOdsRow, ...] | None = None,
    polygons: tuple[AssurPolygon, ...] | None = None,
) -> AssurArtifacts:
    return build_site_artifacts(
        _ASSUR_CONFIG,
        source_revision,
        ods_rows=ods_rows,
        polygons=polygons,
    )


def write_assur_artifacts(output_dir: Path, source_revision: str) -> AssurArtifacts:
    return write_site_artifacts(_ASSUR_CONFIG, output_dir, source_revision)
