from typing import Sequence, List
import argparse
import os
import sys
import json
import pandas as pd
import pymongo
from pymongo import MongoClient
from pymongo.errors import OperationFailure
from ebl.fragmentarium.application.fragment_schema import FragmentSchema
from ebl.fragmentarium.infrastructure.fragment_search_aggregations import (
    sort_by_museum_number,
)
from ebl.mongo_collection import MongoCollection
from ebl.transliteration.infrastructure.collections import FRAGMENTS_COLLECTION

DEV_DB = "ebldev"
PROD_DB = "##ebl##"


parser = argparse.ArgumentParser(
    description="Import documents into the fragments collection"
)
parser.add_argument(
    "--dry-run",
    "--validate",
    action="store_true",
    default=False,
    help="Run validation and exit without updating the db",
)
parser.add_argument(
    "--skip-existing",
    action="store_true",
    default=False,
    help="Skip existing",
)
parser.add_argument(
    "-vv",
    "--verbose",
    action="store_true",
    default=False,
    help="Skip existing",
)
parser.add_argument("fragments", nargs="+")
parser.add_argument(
    "-db",
    "--database",
    choices=[DEV_DB, PROD_DB],
    default=DEV_DB,
    help="Toggle between development (default) and production db",
)


def yellow(text: str) -> str:
    return f"\033[93m{text}\033[0m"


def green(text: str) -> str:
    return f"\033[92m{text}\033[0m"


def red(text: str) -> str:
    return f"\033[91m{text}\033[0m"


def as_error(text: str) -> str:
    return f"{red('Error:')} {text}"


CHECK = green("✔")


def show_progress(info):
    def decorator(f):
        def wrapper(*args, **kwargs):
            print(info, end=" ", flush=True)
            try:
                result = f(*args, **kwargs)
                print(CHECK)
                return result
            except (Exception, SystemExit) as exception:
                print(red("✗"))
                raise exception

        return wrapper

    return decorator


@show_progress("Loading data...")
def load_data(paths: Sequence[str]) -> dict:
    files = [path for path in paths if path.endswith(".json")]
    fragments = {}

    for file in files:
        with open(file) as jsonfile:
            fragments[file] = json.load(jsonfile)

    if not fragments:
        sys.exit(as_error("No framents found."))

    return fragments


@show_progress("Validating data format...")
def validate(fragments: dict) -> None:
    fails = {}

    for filename, data in fragments.items():
        problems = {}

        try:
            problems = FragmentSchema(unknown="exclude").validate(data)
            assert not problems
        except Exception as error:
            fails[filename] = (
                error.__class__.__name__,
                str(problems)[:50] + "[...]" if problems else problems,
            )

    if fails:
        fail_summary_file = os.path.join(
            os.path.dirname(__file__), "invalid_fragments.tsv"
        )

        columns = ["file", "error", "hints"]
        df = pd.DataFrame([[k, *v] for k, v in fails.items()], columns=columns)
        df.to_csv(
            fail_summary_file,
            sep="\t",
            index=False,
        )

        output = as_error(
            "Validation failed. "
            f"See table below or {fail_summary_file} for details.\n\n"
            f"{df.to_markdown(index=False)}\n\nAborting."
        )
        sys.exit(output)


@show_progress("Checking ids...")
def validate_ids(fragments: dict, skip_existing: bool) -> dict:
    new_ids = [data.get("_id") for data in fragments.values()]

    if not all(new_ids):
        output = [as_error("The following documents are missing an '_id' field:")]

        for filename, data in fragments.items():
            if "_id" not in data:
                output.append(filename)

        sys.exit("{}\n\n Aborting.".format("\n".join(output)))

    if existing := [
        data["_id"]
        for data in fragments_collection.find_many(
            {"_id": {"$in": new_ids}}, projection={"_id": True}
        )
    ]:

        if args.skip_existing:
            return {
                filepath: data
                for filepath, data in fragments.items()
                if data["_id"] not in existing
            }
        else:
            fragments_by_id = {
                data["_id"]: filename for filename, data in fragments.items()
            }
            df = pd.DataFrame(
                {"file": [fragments_by_id[_id] for _id in existing], "_id": existing}
            )
            output = as_error(
                f"The following {len(existing)} documents have ids "
                "that already exist in the db:\n\n"
                f"{df.to_markdown(index=False)}\n\n"
            )
            sys.exit(output)

    else:
        return fragments


def push_to_db(fragments: dict, target_db: str) -> List[str]:
    color = green if target_db == DEV_DB else yellow

    is_production_db = target_db == PROD_DB
    if is_production_db:
        prompt = (
            "\n!!! WARNING: This will alter the PRODUCTION DB and can lead to data loss. !!!"
            "\n\nOnly proceed after creating a backup of the fragments collection."
            "\nContinue? (y/n) "
        )
        if input(yellow(prompt)).lower() != "y":
            sys.exit("Aborting.")

    print(f"Starting import into {color(args.database)}...", end=" ")

    try:
        result = fragments_collection.insert_many(fragments.values())
        if not is_production_db:
            print(CHECK)
    except Exception as e:
        print(red("✗"))
        print(
            as_error(
                "Import failed due to the following errors{}:".format(
                    "" if args.verbose else " (use -vv to see the full stack)"
                )
            )
        )

        for error in e.details.get("writeErrors", []):
            print(error.get("errmsg"))

        if args.verbose:
            raise e
        else:
            sys.exit("\nAborting.")

    print("\nSummary of added fragments:", *result, sep="\n")
    print()
    return result


@show_progress("Rebuilding sort index (this may take a moment)...")
def create_sort_index(fragments_collection: MongoCollection) -> None:

    sortkey_index = [("_sortKey", pymongo.ASCENDING)]

    try:
        fragments_collection.drop_index(sortkey_index)
    except OperationFailure:
        print("No index found, creating from scratch...")

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


args = parser.parse_args()

client = MongoClient(os.environ["MONGODB_URI"])
database = client.get_database(args.database)

fragments_collection = MongoCollection(database, FRAGMENTS_COLLECTION)

fragments = load_data(args.fragments)

validate(fragments)
fragments = validate_ids(fragments, args.skip_existing)

if args.dry_run:
    print(green("All good!\n"))
    sys.exit()

push_to_db(fragments, args.database)

create_sort_index(fragments_collection)
