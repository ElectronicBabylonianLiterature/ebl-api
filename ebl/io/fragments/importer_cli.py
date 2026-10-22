import argparse
import datetime
import os
import sys
from typing import Callable, Dict, List, Optional, Sequence, Tuple

from pymongo import MongoClient
from pymongo.database import Database

from ebl.io.fragments.fragment_writer import write_to_db
from ebl.io.fragments.importer import (
    canonicalize,
    create_sort_index,
    ensure_unique,
    load_collection,
    load_data,
    set_word_ids,
    update_sort_keys,
    validate,
    validate_id,
    write_to_tsv,
)
from ebl.mongo_collection import MongoCollection
from ebl.provenance.application.provenance_service import ProvenanceService
from ebl.provenance.infrastructure.mongo_provenance_repository import (
    MongoProvenanceRepository,
)
from ebl.transliteration.infrastructure.collections import FRAGMENTS_COLLECTION

DEV_DB = "ebldev"
PROD_DB = "ebl"
IMPORT_CMD = "import"
VALIDATION_CMD = "validate"
INDEX_CMD = "reindex"
PASSPHRASE = "HAMMURABI"
ERROR_FILE = "invalid_texts.tsv"

Fails = List[List[str]]


def _input_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Parser with input", add_help=False)
    parser.add_argument(
        "fragments",
        nargs="+",
        help="Paths to JSON input files OR a single file with an array of dictionaries",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Abort the import if invalid documents or duplicate IDs are found",
    )
    return parser


def _output_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Parser with output", add_help=False)
    parser.add_argument(
        "-db",
        "--database",
        choices=[DEV_DB, PROD_DB],
        default=DEV_DB,
        help="Toggle between development (default) and production db",
    )
    return parser


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Import documents into the fragments collection. "
            "MONGODB_URI environment variable must be set."
        )
    )
    subparsers = parser.add_subparsers(dest="subcommand", required=True)
    input_parser = _input_parser()
    output_parser = _output_parser()
    for command, info, parents in [
        (
            IMPORT_CMD,
            "Validate input files, write to the database, and reindex",
            [input_parser, output_parser],
        ),
        (
            VALIDATION_CMD,
            "Validate input files without writing to the database",
            [input_parser, output_parser],
        ),
        (INDEX_CMD, "Rebuild the sort index", [output_parser]),
    ]:
        subparsers.add_parser(command, help=info, description=info, parents=parents)
    return parser


def reindex_database(collection: MongoCollection, database_name: str) -> None:
    print(f"Reindexing 'fragments' collection in the {database_name!r} database...")
    print("Calculating _sortKeys (this may take a while)...")
    update_sort_keys(collection)
    print("Creating the sort index...")
    create_sort_index(collection)
    print("Sort index built successfully.")


def load_fragments(paths: Sequence[str]) -> Tuple[Dict[str, dict], bool]:
    if len(paths) == 1:
        try:
            return load_collection(paths[0]), True
        except Exception:
            return load_data(paths), False
    return load_data(paths), False


def check_fragment(
    data: dict,
    filename: str,
    collection: MongoCollection,
    provenance_service: ProvenanceService,
) -> None:
    validate(data, filename, provenance_service)
    validate_id(data, filename)
    ensure_unique(data, collection, filename)


def validate_fragments(
    fragments: Dict[str, dict],
    collection: MongoCollection,
    provenance_service: ProvenanceService,
    strict: bool,
) -> Tuple[Dict[str, dict], Fails]:
    valid: Dict[str, dict] = {}
    fails: Fails = []
    for filename, data in fragments.items():
        try:
            check_fragment(data, filename, collection, provenance_service)
        except Exception as error:
            if strict:
                raise
            fails.append([filename, str(error)])
            continue
        valid[filename] = canonicalize(data, provenance_service)
    return valid, fails


def confirm_production_write(
    database_name: str, read_input: Callable[[str], str] = input
) -> None:
    if database_name != PROD_DB:
        return
    prompt = (
        "\n\033[93m!!! WARNING: "
        "This will alter the PRODUCTION DB and can lead to data loss. !!!"
        "\n\nPROCEED ONLY after creating a DUPLICATE of the fragments collection!\033[0m"
        f"\n\nType {PASSPHRASE} to continue: "
    )
    if read_input(prompt) != PASSPHRASE:
        sys.exit("Aborting.")


def report_validation(fragment_count: int, fails: Fails) -> None:
    if fails:
        print(
            f"Skipping {len(fails)} document(s), "
            f"see {os.path.abspath(ERROR_FILE)} for details"
        )
        write_to_tsv(ERROR_FILE, fails, ["file", "error"])
    print(
        f"Validation of {fragment_count - len(fails)} out of "
        f"{fragment_count} document(s) successful."
    )


def import_fragments(
    valid: Dict[str, dict], collection: MongoCollection, database_name: str
) -> None:
    result = write_to_db(
        [set_word_ids(fragment) for fragment in valid.values()], collection
    )
    print("Result:")
    print(result)
    reindex_database(collection, database_name)
    summary_file = f"fragment_import_summary_{datetime.date.today()}.tsv"
    write_to_tsv(
        summary_file,
        [[data["_id"], filename] for filename, data in valid.items()],
        ["id", "file"],
    )
    print(f"Done! See {os.path.abspath(summary_file)} for a summary of added documents")


def run(
    args: argparse.Namespace,
    database: Database,
    read_input: Callable[[str], str] = input,
) -> None:
    collection = MongoCollection(database, FRAGMENTS_COLLECTION)
    if args.subcommand == INDEX_CMD:
        reindex_database(collection, args.database)
        return
    print("Loading data...")
    fragments, is_collection = load_fragments(args.fragments)
    if not fragments:
        print("No fragments found.")
        return
    print(f"Found {'collection of ' * is_collection}{len(fragments)} documents.")
    print("Validating...")
    provenance_service = ProvenanceService(MongoProvenanceRepository(database))
    valid, fails = validate_fragments(
        fragments, collection, provenance_service, args.strict
    )
    report_validation(len(fragments), fails)
    if not valid:
        print("No data to import.")
        return
    if args.subcommand == VALIDATION_CMD:
        return
    print("Writing to database...")
    confirm_production_write(args.database, read_input)
    import_fragments(valid, collection, args.database)


def main(argv: Optional[Sequence[str]] = None) -> None:
    args = build_parser().parse_args(argv)
    client = MongoClient(os.environ["MONGODB_URI"])
    run(args, client.get_database(args.database))


if __name__ == "__main__":
    main()
