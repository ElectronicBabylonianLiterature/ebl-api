import argparse
from pymongo import MongoClient
from ebl.mongo_collection import MongoCollection
import os
import pandas as pd
from datetime import datetime

# disable false positive SettingsWithCopyWarning
pd.options.mode.chained_assignment = None

client = MongoClient(os.environ["MONGODB_URI"])
DB = os.environ.get("MONGODB_DB")
database = client.get_database("ebl")

output_path = "/workspace/ebl-api/ebl/io"

changelog = MongoCollection(database, "changelog")
fragments = MongoCollection(database, "fragments")

parser = argparse.ArgumentParser()
parser.add_argument(
    "-for", "--names", nargs="+", help="Names of workers", required=True
)
parser.add_argument("-in", "--month", help="Month to include", required=True)


def aggregate_actions(names, month, year):
    return [
        {"$match": {"user_profile.nickname": {"$regex": "|".join(names)}}},
        {"$addFields": {"date": {"$toDate": "$date"}}},
        {
            "$match": {
                "$expr": {
                    "$and": [
                        {"$eq": [year, {"$year": "$date"}]},
                        {"$eq": [month, {"$month": "$date"}]},
                    ]
                },
                "resource_type": "fragments",
            }
        },
        {"$sort": {"date": -1}},
        {"$unwind": "$diff"},
        {
            "$project": {
                "_id": 0,
                "user": "$user_profile.nickname",
                "action": {"$first": "$diff"},
                "edits": {"$last": "$diff"},
                "field": {"$arrayElemAt": ["$diff", 1]},
                "date": 1,
                "resource_id": 1,
            }
        },
        {"$unwind": "$field"},
        {
            "$match": {
                "field": {
                    "$in": [
                        "lines",
                        "references",
                        "introduction",
                        "notes",
                        "script.period",
                    ]
                }
            }
        },
        {
            "$group": {
                "_id": {"resource_id": "$resource_id", "action": "$action"},
                "user": {"$first": "$user"},
                "fields": {"$addToSet": "$field"},
            }
        },
        {
            "$project": {
                "_id": 0,
                "resource_id": "$_id.resource_id",
                "action": "$_id.action",
                "user": 1,
                "fields": "$fields",
            }
        },
    ]


def fetch_first_references(museum_numbers):
    return fragments.aggregate(
        [
            {"$match": {"_id": {"$in": museum_numbers}}},
            {
                "$project": {
                    "_id": 0,
                    "resource_id": "$_id",
                    "reference": {"$first": "$references.id"},
                }
            },
        ]
    )


if __name__ == "__main__":
    args = parser.parse_args()
    if "." in args.month:
        month, year = map(int, args.month.split("."))
    else:
        month = int(args.month.lstrip("0"))
        year = datetime.today().year

    data = changelog.aggregate(aggregate_actions(args.names, month, year))
    df = pd.DataFrame.from_records(data)
    df = df[df.resource_id != "Test.Fragment"]
    df = df.explode("fields").sort_values(["resource_id", "fields"])

    df = df.groupby(["user", "resource_id", "fields"]).agg({"action": "/".join})

    df = df.reset_index()
    df["action"] = df.action + " " + df.fields
    df = df.drop("fields", axis=1)
    df = df.groupby(["user", "resource_id"]).agg("; ".join).reset_index()
    df["date"] = f"{year}.{month}"
    df = df.rename_axis("Index").reset_index()
    df.Index += 1
    df = df[["date", "user", "Index", "resource_id", "action"]]

    df_ref = pd.DataFrame.from_records(fetch_first_references(df.resource_id.to_list()))

    print(df)
    print(df_ref)
    print(df.merge(df_ref, on="resource_id").fillna(""))

    # groupby user, export into excel file
