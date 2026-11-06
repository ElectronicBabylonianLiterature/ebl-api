import sys

from ebl.fragmentarium.application.map_artifact_cli import (
    main as generate_site_artifacts,
)


def main(argv: list[str] | None = None) -> int:
    arguments = sys.argv[1:] if argv is None else argv
    return generate_site_artifacts(["--site", "ASSUR", *arguments])


if __name__ == "__main__":
    raise SystemExit(main())
