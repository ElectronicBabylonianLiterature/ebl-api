from typing import Sequence, List
import argparse
import os
import sys
import json
from marshmallow import ValidationError
import pymongo
from pymongo import MongoClient
from pymongo.errors import OperationFailure
from ebl.fragmentarium.application.fragment_schema import FragmentSchema
from ebl.fragmentarium.infrastructure.fragment_search_aggregations import (
    sort_by_museum_number,
)
from ebl.mongo_collection import MongoCollection
from ebl.transliteration.domain.museum_number import MuseumNumber
from ebl.transliteration.infrastructure.collections import FRAGMENTS_COLLECTION


def load_data(paths: Sequence[str]) -> dict:
    files = [path for path in paths if path.endswith(".json")]
    fragments = {}

    for file in files:
        with open(file) as jsonfile:
            try:
                fragments[file] = json.load(jsonfile)
            except json.JSONDecodeError as error:
                raise ValueError(f"Invalid JSON: {file}") from error

    if not fragments:
        print("No fragments found.")
        sys.exit()

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


def create_sort_index(fragments_collection: MongoCollection) -> None:
    sortkey_index = [("_sortKey", pymongo.ASCENDING)]

    try:
        fragments_collection.drop_index(sortkey_index)
    except OperationFailure:
        pass

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
    fragments_collection.create_index(sortkey_index)


def write_to_db(
    fragments: Sequence[dict], fragments_collection: MongoCollection
) -> List:

    return fragments_collection.insert_many(fragments, ordered=False)


if __name__ == "__main__":
    DEV_DB = "ebldev"
    PROD_DB = "ebl"

    parser = argparse.ArgumentParser(
        description="Import documents into the fragments collection."
    )
    parser.add_argument(
        "--dry-run",
        "--validate",
        action="store_true",
        default=False,
        help="Run validation and exit without updating the db",
    )
    parser.add_argument("fragments", nargs="+")
    parser.add_argument(
        "-db",
        "--database",
        choices=[DEV_DB, PROD_DB],
        default=DEV_DB,
        help="Toggle between development (default) and production db",
    )

    args = parser.parse_args()

    CLIENT = MongoClient(os.environ["MONGODB_URI"])
    TARGET_DB = CLIENT.get_database(args.database)

    COLLECTION = MongoCollection(TARGET_DB, FRAGMENTS_COLLECTION)

    fragments_to_import = load_data(args.fragments)

    print("Validating...")

    for filename, data in fragments_to_import.items():
        validate(data, filename)
        validate_id(data, filename)
        ensure_unique(data, COLLECTION, filename)

    print("Validation successful.")

    if args.dry_run:
        sys.exit()

    print("Writing to database...")

    if TARGET_DB == PROD_DB:
        prompt = (
            "\n!!! WARNING: This will alter the PRODUCTION DB and can lead to data loss. !!!"
            "\n\nOnly proceed if you created a backup of the fragments collection."
            "\nType YES to continue: "
        )
        if input(prompt) != "YES":
            sys.exit("Aborting.")

    result = write_to_db(list(fragments_to_import.values()), COLLECTION)

    print("Result:")
    print(result)

    print("Updating sort index (this may take a while...)")

    create_sort_index(COLLECTION)

    print("Done! The following fragments were added:")
    for filename, data in fragments_to_import.items():
        print(data["_id"], filename, sep="\t")
