from __future__ import annotations

import argparse
from pathlib import Path
from typing import Optional, Sequence

from pymongo import MongoClient
from pymongo.uri_parser import parse_uri

from ebl.bibliography.application.duplicate_audit import run_audit

LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1"}
PRODUCTION_DATABASES = {"ebl", "production", "prod"}
PRODUCTION_HOST_MARKERS = ("prod", "production")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the read-only bibliography duplicate audit."
    )
    parser.add_argument("--mongo-uri", required=True)
    parser.add_argument("--database", required=True)
    parser.add_argument(
        "--output-dir",
        default="bibliography-duplicate-audit",
        type=Path,
    )
    parser.add_argument("--review-overrides", type=Path)
    parser.add_argument("--allow-non-local-read", action="store_true")
    parser.add_argument("--allow-production-read", action="store_true")
    return parser


def uri_hosts(mongo_uri: str) -> set[str]:
    try:
        parsed = parse_uri(mongo_uri)
    except Exception as error:
        raise ValueError("Invalid MongoDB URI.") from error
    return {host for host, _port in parsed.get("nodelist", [])}


def is_local_host(host: str) -> bool:
    return host in LOCAL_HOSTS or host.startswith("127.")


def is_production_like(hosts: set[str], database: str) -> bool:
    normalized_database = database.casefold()
    normalized_hosts = {host.casefold() for host in hosts}
    return normalized_database in PRODUCTION_DATABASES or any(
        marker in host
        for marker in PRODUCTION_HOST_MARKERS
        for host in normalized_hosts
    )


def validate_read_target(
    mongo_uri: str,
    database: str,
    *,
    allow_non_local_read: bool = False,
    allow_production_read: bool = False,
) -> None:
    hosts = uri_hosts(mongo_uri)
    if not hosts:
        raise ValueError("MongoDB URI does not include any hosts.")
    if not all(is_local_host(host) for host in hosts) and not allow_non_local_read:
        raise PermissionError(
            "Refusing non-local MongoDB read without --allow-non-local-read."
        )
    if is_production_like(hosts, database) and not allow_production_read:
        raise PermissionError(
            "Refusing production-looking MongoDB read without --allow-production-read."
        )


def run_from_args(args: argparse.Namespace) -> int:
    validate_read_target(
        args.mongo_uri,
        args.database,
        allow_non_local_read=args.allow_non_local_read,
        allow_production_read=args.allow_production_read,
    )
    client = MongoClient(args.mongo_uri)
    try:
        pairs, groups = run_audit(
            client[args.database],
            args.output_dir,
            args.review_overrides,
        )
    finally:
        client.close()
    print(
        "Bibliography duplicate audit complete: "
        f"{len(pairs)} candidate pairs, {len(groups)} candidate groups. "
        f"Reports written to {args.output_dir}."
    )
    return 0


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return run_from_args(args)
    except (PermissionError, ValueError) as error:
        parser.error(str(error))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
