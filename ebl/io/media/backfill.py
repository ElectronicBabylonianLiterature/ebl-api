import argparse
import hashlib
import json
import os
import sys
from pathlib import Path
from urllib.parse import urlsplit
from pymongo import MongoClient
from pymongo.errors import PyMongoError
from ebl.io.media.backfill_commands import MigrationRunOptions, apply_plan, dry_run
from ebl.io.media.backfill_plan_file import inspect_plan
from ebl.media.application.backfill_plan import BackfillPolicy
from ebl.media.application.media_requests import BackfillRequest
from ebl.media.infrastructure.backfill_runner import LegacyPhotoMigration
from ebl.media.infrastructure.backfill_sources import LegacyPhotoSources
from ebl.media.infrastructure.backfill_preflight import prepare_legacy_indexes
from ebl.media.infrastructure.grid_fs_media_representation_store import (
    GridFsMediaRepresentationStore,
)
from ebl.media.infrastructure.mongo_media_repository import MongoMediaRepository


def parser() -> argparse.ArgumentParser:
    argument_parser = argparse.ArgumentParser(
        description="Plan or apply protected legacy photo imports."
    )
    commands = argument_parser.add_subparsers(dest="command", required=True)
    for command in ("dry-run", "apply", "prepare-indexes"):
        command_parser = commands.add_parser(command)
        command_parser.add_argument("--database", required=True)
        command_parser.add_argument("--uri-env", default="MONGODB_URI")
        if command != "dry-run":
            command_parser.add_argument("--confirm-database", required=True)
        if command != "prepare-indexes":
            command_parser.add_argument("--report", required=True, type=Path)
            command_parser.add_argument("--resume", action="store_true")
        if command == "dry-run":
            command_parser.add_argument("--batch-size", type=int, default=100)
            command_parser.add_argument("--max-batches", type=int)
            command_parser.add_argument("--generate-previews", action="store_true")
            command_parser.add_argument(
                "--no-map-attribution", dest="map_attribution", action="store_false"
            )
        elif command == "apply":
            command_parser.add_argument("--plan", required=True, type=Path)
            command_parser.add_argument("--limit", type=int)
            command_parser.add_argument(
                "--confirm-source-writes-paused", action="store_true", required=True
            )
    return argument_parser


def target_identity(uri: str, database: str) -> dict:
    parsed = urlsplit(uri)
    if parsed.scheme not in {"mongodb", "mongodb+srv"} or not parsed.netloc:
        raise ValueError("MongoDB URI must identify an explicit endpoint.")
    endpoint = parsed.scheme + "://" + parsed.netloc.rsplit("@", 1)[-1].lower()
    return {
        "database": database,
        "endpointSha256": hashlib.sha256(endpoint.encode()).hexdigest(),
    }


def policy_for(arguments: argparse.Namespace) -> BackfillPolicy:
    if arguments.command == "apply":
        header, _digest = inspect_plan(arguments.plan)
        return BackfillPolicy.of(header["policy"])
    return BackfillPolicy(
        generate_previews=getattr(arguments, "generate_previews", False),
        map_attribution=getattr(arguments, "map_attribution", True),
    )


def validate_arguments(arguments: argparse.Namespace) -> None:
    if not arguments.database.strip():
        raise ValueError("Database name must be explicit and nonempty.")
    if (
        arguments.command != "dry-run"
        and arguments.confirm_database != arguments.database
    ):
        raise ValueError("Database confirmation does not match the target.")
    if arguments.command == "dry-run":
        BackfillRequest(batch_size=arguments.batch_size)
    for field in ("limit", "max_batches"):
        value = getattr(arguments, field, None)
        if value is not None and value < 1:
            raise ValueError("Processing limits must be positive.")
    if (
        arguments.command == "apply"
        and arguments.plan.resolve() == arguments.report.resolve()
    ):
        raise ValueError("Apply reports must not overwrite their source plan.")


def execute(arguments: argparse.Namespace) -> dict:
    validate_arguments(arguments)
    uri = os.environ.get(arguments.uri_env)
    if not uri:
        raise ValueError("The selected MongoDB URI environment variable is unset.")
    target = target_identity(uri, arguments.database)
    policy = policy_for(arguments)
    client: MongoClient = MongoClient(uri, serverSelectionTimeoutMS=10000)
    with client:
        database = client[arguments.database]
        repository = MongoMediaRepository(database)
        store = GridFsMediaRepresentationStore(database)
        migration = LegacyPhotoMigration(
            LegacyPhotoSources(database), repository, store, policy
        )
        if arguments.command == "prepare-indexes":
            repository.assert_writable_topology()
            prepare_legacy_indexes(database)
            repository.create_indexes()
            store.create_indexes()
            return dict(target, indexesPrepared=True)
        if arguments.command == "apply":
            repository.assert_writable_topology()
            return apply_plan(
                migration,
                arguments.plan,
                MigrationRunOptions(
                    arguments.report, target, arguments.resume, limit=arguments.limit
                ),
            )
        return dry_run(
            migration,
            MigrationRunOptions(
                arguments.report,
                target,
                arguments.resume,
                batch_size=arguments.batch_size,
                max_batches=arguments.max_batches,
            ),
        )


def main(argv: list[str] | None = None) -> int:
    try:
        result = execute(parser().parse_args(argv))
    except (ValueError, OSError, PyMongoError) as error:
        print(
            f"Media migration stopped ({type(error).__name__}); no progress beyond the durable report is claimed.",
            file=sys.stderr,
        )
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0 if result.get("complete", True) and not result.get("pendingSources") else 2


if __name__ == "__main__":
    raise SystemExit(main())
