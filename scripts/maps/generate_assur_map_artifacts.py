#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from ebl.fragmentarium.application.assur_map_artifacts import (  # noqa: E402
    DEFAULT_OUTPUT_DIR,
    write_assur_artifacts,
)


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate deterministic Aššur map artifacts"
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
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    artifacts = write_assur_artifacts(args.output_dir, args.source_revision)
    print("Generated Aššur map artifacts")
    print("Inventory:", len(artifacts["inventory"]))
    print("Mappings:", len(artifacts["mappings"]))
    print("Curation rows:", len(artifacts["curation"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
