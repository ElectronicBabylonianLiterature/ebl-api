from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
from typing import TypedDict
from urllib.error import URLError
from urllib.request import Request, urlopen

from ebl.fragmentarium.application.map_json import is_bson_int64, load_strict_json
from scripts.maps.map_membership import MEMBERSHIP_PATH

SOURCE_URL = "https://www.ebl.lmu.de/api/findspots"


class MembershipRow(TypedDict):
    findspotId: int
    siteName: str | None


class MembershipSnapshot(TypedDict):
    schemaVersion: int
    source: str
    sourceRevision: str
    fetchedAt: str
    etag: str | None
    findspots: list[MembershipRow]


def build_membership_snapshot(
    response: bytes, fetched_at: str, etag: str | None = None
) -> MembershipSnapshot:
    payload = load_strict_json(response.decode("utf-8"), SOURCE_URL)
    if not isinstance(payload, list):
        raise ValueError("Canonical findspot response must be a JSON array.")
    rows: list[MembershipRow] = []
    for record in payload:
        if not isinstance(record, dict) or "_id" not in record or "site" not in record:
            raise ValueError("Canonical findspot records require _id and site fields.")
        findspot_id, site = record["_id"], record["site"]
        if not is_bson_int64(findspot_id):
            raise ValueError("Canonical findspot IDs must be BSON int64s.")
        if site is not None and (not isinstance(site, str) or not site.strip()):
            raise ValueError("Canonical site names must be nonblank strings or null.")
        rows.append({"findspotId": findspot_id, "siteName": site})
    return {
        "schemaVersion": 1,
        "source": SOURCE_URL,
        "sourceRevision": "sha256:" + hashlib.sha256(response).hexdigest(),
        "fetchedAt": fetched_at,
        "etag": etag,
        "findspots": sorted(
            rows, key=lambda row: (row["findspotId"], row["siteName"] or "")
        ),
    }


def fetch_response() -> tuple[bytes, str | None]:
    request = Request(SOURCE_URL, headers={"Accept": "application/json"})
    with urlopen(request, timeout=30) as response:
        return response.read(), response.headers.get("ETag")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Refresh map membership evidence from the canonical findspot API"
    )
    parser.add_argument("--output", type=Path, default=MEMBERSHIP_PATH)
    parser.add_argument("--response-file", type=Path)
    parser.add_argument("--fetched-at")
    parser.add_argument("--etag")
    args = parser.parse_args(argv)
    try:
        if args.response_file is None:
            response, etag = fetch_response()
        else:
            response, etag = args.response_file.read_bytes(), args.etag
        fetched_at = args.fetched_at or datetime.now(timezone.utc).isoformat(
            timespec="milliseconds"
        ).replace("+00:00", "Z")
        snapshot = build_membership_snapshot(response, fetched_at, etag)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
    except (ValueError, OSError, URLError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    print(f"Wrote {len(snapshot['findspots'])} membership rows to {args.output}")
    print(snapshot["sourceRevision"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
