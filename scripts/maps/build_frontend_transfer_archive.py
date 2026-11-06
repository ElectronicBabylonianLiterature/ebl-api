#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from ebl.fragmentarium.application.map_artifact_generator import (  # noqa: E402
    DEFAULT_OUTPUT_DIR,
)
from scripts.maps.frontend_transfer_archive import build_archive  # noqa: E402


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build the multi-site frontend-transfer archive"
    )
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(tempfile.gettempdir())
        / "map-multi-site-canonical-artifacts.tar.gz",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    output_path = build_archive(args.data_dir, args.output)
    print(f"Wrote {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
