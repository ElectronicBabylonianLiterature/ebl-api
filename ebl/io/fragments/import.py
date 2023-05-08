import argparse
import os
import sys
import json
import pandas as pd
import pymongo
from pymongo import MongoClient
from pymongo.errors import OperationFailure
from ebl.errors import DataError
from ebl.fragmentarium.application.fragment_schema import FragmentSchema
from ebl.fragmentarium.infrastructure.fragment_search_aggregations import (
    sort_by_museum_number,
)
from ebl.mongo_collection import MongoCollection
from ebl.transliteration.infrastructure.collections import FRAGMENTS_COLLECTION

# from marshmallow import ValidationError

DEV_DB = "ebldev"
PROD_DB = "##ebl##"

parser = argparse.ArgumentParser(
    description="Import documents into the fragments collection"
)
parser.add_argument(
    "--dry-run",
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

client = MongoClient(os.environ["MONGODB_URI"])
database = client.get_database(args.database)

fragments_collection = MongoCollection(database, FRAGMENTS_COLLECTION)


def _create_sort_index(self) -> None:
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


files = [path for path in args.fragments if path.endswith(".json")]
n = len(files)

print(f"Starting import of {n} fragments...")

fragments = {}

for file in files:
    with open(file) as jsonfile:
        fragments[file] = json.load(jsonfile)


print("Validating...")

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


number_of_fails = len(fails)

print(f"Successful: {n - number_of_fails}")
print(f"Failed: {number_of_fails}")


if fails:
    fail_summary_file = os.path.join(os.path.dirname(__file__), "invalid_fragments.tsv")
    print(
        f"Aborting: invalid input. See table below or {fail_summary_file} for details."
    )
    columns = ["file", "error", "hints"]
    df = pd.DataFrame([[k, *v] for k, v in fails.items()], columns=columns)
    df.to_csv(
        fail_summary_file,
        sep="\t",
        index=False,
    )
    print()
    print(df.to_markdown(index=False), end="\n\n")
    # sys.exit()

# check if any of the ids exists, throw error if yes

new_ids = [data["_id"] for data in fragments if "_id" in data]
assert new_ids

if existing_ids := fragments_collection.count_documents({"_id": {"$in": new_ids}}):
    raise DataError(f"Found {existing_ids} existing ids in the db")


if args.dry_run:
    print("All good! Run the command without --dry-run to perform the import.")
    sys.exit()

print("Importing documents into the db...")
# insert the documents into the db - option to skip existing ids?

print("Rebuilding sort index...")
