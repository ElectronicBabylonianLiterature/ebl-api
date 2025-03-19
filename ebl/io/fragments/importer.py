from typing import Optional, Sequence, List
import argparse
import os
import sys
import json
from marshmallow import ValidationError
from pymongo import MongoClient
import pymongo
from ebl.common.query.util import sort_by_museum_number
from ebl.fragmentarium.application.fragment_schema import FragmentSchema
from ebl.mongo_collection import MongoCollection
from ebl.transliteration.domain.museum_number import MuseumNumber
from ebl.transliteration.infrastructure.collections import FRAGMENTS_COLLECTION
import csv
import datetime
from .sitemap_updater import update_sitemap_in_frontend


def _load_json(path: str):
    with open(path) as jsonfile:
        try:
            return json.load(jsonfile)
        except json.JSONDecodeError as error:
            raise ValueError(f"Invalid JSON: {path}") from error


def assert_type(obj, expected_type, prefix=""):
    if not isinstance(obj, expected_type):
        prefix = f"{prefix} " if prefix else ""
        raise ValueError(
            f"{prefix}Expected {expected_type} but got {type(obj)} instead"
        )


def load_data(paths: Sequence[str]) -> dict:
    return {file: _load_json(file) for file in paths if file.endswith(".json")}


def load_collection(path: str) -> dict:
    fragments = {}

    if not path.endswith(".json"):
        return fragments

    collection = _load_json(path)

    assert_type(collection, list)

    for index, data in enumerate(collection):
        assert_type(data, dict)
        fragments[f"{path}[{index}]"] = data

    return fragments


def validate(data: dict, filename="") -> None:
    try:
        validation_errors = FragmentSchema(unknown="exclude").validate(data)
    except Exception as error:
        raise ValidationError(f"Invalid data in {filename}: {error}") from error
    if validation_errors:
        raise ValidationError(f"Invalid data in {filename}: {validation_errors}")


def validate_id(data: dict, filename="") -> None:
    if "_id" not in data:
        raise ValidationError(f"Missing _id in {filename}")

    try:
        MuseumNumber.of(data["_id"])
    except ValueError:
        raise ValidationError(
            f"id {data['_id']!r} of {filename} is not a valid museum number"
        )


def ensure_unique(
    data: dict, fragments_collection: MongoCollection, filename=""
) -> None:
    data_by_id = (
        data["_id"]
        for data in fragments_collection.find_many(
            {"_id": data["_id"]}, projection={"_id": True}
        )
    )
    if existing := next(
        data_by_id,
        False,
    ):
        raise ValidationError(f"ID {existing} of file {filename} already exists")


def update_sort_keys(fragments_collection: MongoCollection) -> None:
    fragments_collection.aggregate(
        [
            {"$project": {"museumNumber": True}},
            *sort_by_museum_number(),
            {
                "$group": {
                    "_id": None,
                    "sorted": {"$push": "$_id"},
                }
            },
            {"$unwind": {"path": "$sorted", "includeArrayIndex": "sortKey"}},
            {"$project": {"_id": "$sorted", "_sortKey": "$sortKey"}},
            {"$merge": "fragments"},
        ],
        allowDiskUse=True,
    )


def create_sort_index(fragments_collection: MongoCollection) -> None:
    fragments_collection.create_index([("_sortKey", pymongo.ASCENDING)])


def write_to_db(
    fragments: Sequence[dict], fragments_collection: MongoCollection
) -> List:
    return fragments_collection.insert_many(fragments, ordered=False)


def write_to_tsv(
    filepath: str,
    data: Sequence[Sequence[str]],
    column_names: Optional[Sequence[str]] = None,
) -> None:
    with open(filepath, "w", newline="") as csvfile:
        writer = csv.writer(csvfile, delimiter="\t")  # pyre-ignore[6]
        if column_names:
            writer.writerow(column_names)
        writer.writerows(FAILS)


if __name__ == "__main__":
    DEV_DB = "ebldev"
    PROD_DB = "ebl"
    IMPORT_CMD = "import"
    VALIDATION_CMD = "validate"
    INDEX_CMD = "reindex"
    UPDATE_SITEMAP_CMD = "update-sitemap"

    parser = argparse.ArgumentParser(
        description=(
            "Import documents into the fragments collection. "
            "MONGODB_URI environment variable must be set."
        )
    )
    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    _input_parser = argparse.ArgumentParser(
        description="Parser with input", add_help=False
    )
    _input_parser.add_argument(
        "fragments",
        nargs="+",
        help="Paths to JSON input files OR a single file with an array of dictionaries",
    )
    _input_parser.add_argument(
        "--strict",
        action="store_true",
        help="Abort the import if invalid documents or duplicate IDs are found",
    )
    _output_parser = argparse.ArgumentParser(
        description="Parser with output", add_help=False
    )
    _output_parser.add_argument(
        "-db",
        "--database",
        choices=[DEV_DB, PROD_DB],
        default=DEV_DB,
        help="Toggle between development (default) and production db",
    )

    import_info = "Validate input files, write to the database, and reindex"
    import_parser = subparsers.add_parser(
        IMPORT_CMD,
        help=import_info,
        description=import_info,
        parents=[_input_parser, _output_parser],
    )

    validation_info = "Validate input files without writing to the database"
    validation_parser = subparsers.add_parser(
        VALIDATION_CMD,
        help=validation_info,
        description=validation_info,
        parents=[_input_parser, _output_parser],
    )

    index_info = "Rebuild the sort index"
    index_parser = subparsers.add_parser(
        INDEX_CMD,
        help=index_info,
        description=index_info,
        parents=[_output_parser],
    )

    update_sitemap_info = "Update sitemap in ebl-frontend"
    update_sitemap_parser = subparsers.add_parser(
        UPDATE_SITEMAP_CMD,
        help=update_sitemap_info,
        description=update_sitemap_info,
        parents=[_output_parser],
    )

    def _reindex_database(collection, db):
        print(f"Reindexing 'fragments' collection in the {db!r} database...")
        print("Calculating _sortKeys (this may take a while)...")
        update_sort_keys(collection)

        print("Creating the sort index...")
        create_sort_index(collection)

        print("Sort index built successfully.")

    args = parser.parse_args()

    CLIENT = MongoClient(os.environ["MONGODB_URI"])
    TARGET_DB = CLIENT.get_database(args.database)
    COLLECTION = MongoCollection(TARGET_DB, FRAGMENTS_COLLECTION)
    INVALID = set()
    DUPLICATES = set()
    FAILS = []
    IS_COLLECTION = False

    error_file = "invalid_texts.tsv"
    summary_file = f"fragment_import_summary_{datetime.date.today()}.tsv"

    if args.subcommand == INDEX_CMD:
        _reindex_database(COLLECTION, args.database)
        sys.exit()

    if args.subcommand == UPDATE_SITEMAP_CMD:
        update_sitemap_in_frontend()
        sys.exit()

    print("Loading data...")

    if len(args.fragments) == 1:
        try:
            fragments = load_collection(args.fragments[0])
            IS_COLLECTION = True
        except Exception:
            fragments = load_data(args.fragments)

    else:
        fragments = load_data(args.fragments)

    fragment_count = len(fragments)

    if fragments:
        print(f"Found {'collection of ' * IS_COLLECTION}{fragment_count} documents.")
    else:
        print("No fragments found.")
        sys.exit()

    print("Validating...")

    for filename, data in fragments.items():
        if args.strict:
            validate(data, filename)
            validate_id(data, filename)
            ensure_unique(data, COLLECTION, filename)
        else:
            try:
                validate(data, filename)
                validate_id(data, filename)
            except Exception as error:
                FAILS.append([filename, str(error)])
                continue
            try:
                ensure_unique(data, COLLECTION, filename)
            except Exception as error:
                FAILS.append([filename, str(error)])

    fail_count = len(FAILS)

    if FAILS:
        print(
            f"Skipping {fail_count} document(s), see {os.path.abspath(error_file)} for details"
        )
        write_to_tsv(error_file, FAILS, ["file", "error"])

    valid_count = fragment_count - fail_count

    print(
        f"Validation of {valid_count} out of {fragment_count} document(s) successful."
    )

    if not valid_count:
        print("No data to import.")
        sys.exit()

    if args.subcommand == VALIDATION_CMD:
        sys.exit()

    print("Writing to database...")

    if args.database == PROD_DB:
        passphrase = "HAMMURABI"
        prompt = (
            "\n\033[93m!!! WARNING: "
            "This will alter the PRODUCTION DB and can lead to data loss. !!!"
            "\n\nPROCEED ONLY after creating a DUPLICATE of the fragments collection!\033[0m"
            f"\n\nType {passphrase} to continue: "
        )
        if input(prompt) != passphrase:
            sys.exit("Aborting.")

    fragments = {
        filename: data
        for filename, data in fragments.items()
        if filename not in {file for file, _ in FAILS}
    }
    result = write_to_db(
        list(fragments.values()),
        COLLECTION,
    )

    print("Result:")
    print(result)

    _reindex_database(COLLECTION, args.database)

    write_to_tsv(
        summary_file,
        [[data["_id"], filename] for filename, data in fragments.items()],
        ["id", "file"],
    )

    print(
        f"Done! See {os.path.abspath(summary_file)} for a summary of added documents",
    )
