from typing import Sequence, List
import argparse
import os
import sys
import json
from marshmallow import ValidationError
from pymongo import MongoClient
import pymongo
from ebl.fragmentarium.application.fragment_schema import FragmentSchema
from ebl.fragmentarium.infrastructure.fragment_search_aggregations import (
    sort_by_museum_number,
)
from ebl.mongo_collection import MongoCollection
from ebl.transliteration.domain.museum_number import MuseumNumber
from ebl.transliteration.infrastructure.collections import FRAGMENTS_COLLECTION


def load_data(paths: Sequence[str]) -> dict:
    fragments = {}

    for file in paths:
        if not file.endswith(".json"):
            continue

        with open(file) as jsonfile:
            try:
                fragments[file] = json.load(jsonfile)
            except json.JSONDecodeError as error:
                raise ValueError(f"Invalid JSON: {file}") from error

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


if __name__ == "__main__":
    DEV_DB = "ebldev"
    PROD_DB = "ebl"
    IMPORT_CMD = "import"
    VALIDATION_CMD = "validate"
    INDEX_CMD = "reindex"

    parser = argparse.ArgumentParser(
        description=(
            "Import documents into the fragments collection. "
            "MONGODB_URI environment variable must be set."
        )
    )
    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    import_info = "Validate input files, write to the database, and reindex"
    import_parser = subparsers.add_parser(
        IMPORT_CMD, help=import_info, description=import_info
    )

    validation_info = "Validate input files without writing to the database"
    validation_parser = subparsers.add_parser(
        VALIDATION_CMD, help=validation_info, description=validation_info
    )

    for parser_with_input in [import_parser, validation_parser]:
        parser_with_input.add_argument(
            "fragments", nargs="+", help="Paths to JSON input files"
        )

    index_info = "Rebuild the sort index"
    index_parser = subparsers.add_parser(
        INDEX_CMD, help=index_info, description=index_info
    )

    parser.add_argument(
        "-db",
        "--database",
        choices=[DEV_DB, PROD_DB],
        default=DEV_DB,
        help="Toggle between development (default) and production db",
    )

    def reindex_database(collection):
        print("Calculating _sortKeys (this may take a while)...")
        update_sort_keys(collection)

        print("Reindexing database...")
        create_sort_index(collection)

        print("Sort index built successfully.")

    args = parser.parse_args()

    CLIENT = MongoClient(os.environ["MONGODB_URI"])
    TARGET_DB = CLIENT.get_database(args.database)

    COLLECTION = MongoCollection(TARGET_DB, FRAGMENTS_COLLECTION)

    if args.subcommand == INDEX_CMD:
        reindex_database(COLLECTION)
        sys.exit()

    print("Loading data...")
    fragments = load_data(args.fragments)

    if fragments:
        print(f"Found {len(fragments)} files.")
    else:
        print("No fragments found.")
        sys.exit()

    print("Validating...")

    for filename, data in fragments.items():
        validate(data, filename)
        validate_id(data, filename)
        ensure_unique(data, COLLECTION, filename)

    print("Validation successful.")

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

    result = write_to_db(list(fragments.values()), COLLECTION)

    print("Result:")
    print(result)

    reindex_database(COLLECTION)

    print("Done! Summary of added fragments:")
    for filename, data in fragments.items():
        print(data["_id"], filename, sep="\t")
