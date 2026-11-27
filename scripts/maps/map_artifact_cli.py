from __future__ import annotations

import argparse
import sys
from pathlib import Path
from scripts.maps.map_artifact_generator import (
    DEFAULT_OUTPUT_DIR,
    write_site_artifacts,
)
from scripts.maps.map_site_config import SITE_CONFIGS


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate deterministic findspot map artifacts for one site"
    )
    parser.add_argument(
        "--site",
        required=True,
        choices=sorted(SITE_CONFIGS),
        help="Canonical site identifier",
    )
    parser.add_argument(
        "--source-revision",
        required=True,
        help="Revision label to embed in generated mapping records",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Directory to receive generated artifacts",
    )
    parser.add_argument(
        "--curated",
        type=Path,
        default=None,
        help="Path to a reviewed curated-mapping JSON file for this site",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    config = SITE_CONFIGS[args.site]
    try:
        artifacts = write_site_artifacts(
            config, args.output_dir, args.source_revision, args.curated
        )
    except ValueError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    print(f"Generated {config.site_name} map artifacts")
    print("Inventory:", len(artifacts["inventory"]))
    print("Mappings:", len(artifacts["mappings"]))
    print("Curation rows:", len(artifacts["curation"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
