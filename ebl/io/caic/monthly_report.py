import argparse
import os
from datetime import datetime
from typing import Sequence

import pandas as pd
from pymongo import MongoClient

from ebl.mongo_collection import MongoCollection
from ebl.transliteration.domain.museum_number import MuseumNumber

# disable false positive SettingsWithCopyWarning
pd.options.mode.chained_assignment = None

client = MongoClient(os.environ["MONGODB_URI"])
DB = os.environ.get("MONGODB_DB")
database = client.get_database("ebl")

changelog = MongoCollection(database, "changelog")
fragments = MongoCollection(database, "fragments")

parser = argparse.ArgumentParser()
parser.add_argument("-for", "--names", nargs="+", help="Names of workers")
parser.add_argument(
    "-in",
    "--month",
    help="Month to include: either a single integer 1-12 or with year, e.g., 12.2022",
    default=str(datetime.today().month),
)

month_names = [
    "",
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
]

include_fields = [
    "text",
    "signs",
    "lines",
    "references",
    "introduction",
    "notes",
    "script",
    "uniqueLemma",
]


def aggregate_actions(names: Sequence[str], month: int, year: int):
    pipeline = [
        {
            "$match": {
                "resource_type": "fragments",
                "user_profile.nickname": {"$regex": "|".join(names)},
            }
        },
        {"$addFields": {"date": {"$toDate": "$date"}}},
        {
            "$match": {
                "$expr": {
                    "$and": [
                        {"$eq": [year, {"$year": "$date"}]},
                        {"$eq": [month, {"$month": "$date"}]},
                    ]
                },
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
        {"$match": {"field": {"$regex": "|".join(include_fields)}}},
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

    return changelog.aggregate(pipeline)


def aggregate_references(museum_numbers: Sequence[str]):
    pipeline = [
        {"$match": {"_id": {"$in": museum_numbers}}},
        {"$project": {"references": True}},
        {"$unwind": "$references"},
        {"$addFields": {"isCopy": {"$eq": ["$references.type", "COPY"]}}},
        {"$sort": {"isCopy": -1}},
        {
            "$group": {
                "_id": {
                    "resource_id": "$_id",
                },
                "resource_id": {"$first": "$_id"},
                "reference": {"$first": "$references.id"},
                "pages": {"$first": "$references.pages"},
            }
        },
        {"$project": {"_id": 0}},
    ]

    return fragments.aggregate(pipeline)


if __name__ == "__main__":
    args = parser.parse_args()

    if "." in args.month:
        month, year = map(int, args.month.split("."))
    else:
        month = int(args.month.lstrip("0"))
        year = datetime.today().year

    if month not in range(1, 13):
        raise ValueError("")

    users = args.names or [
        name for name in os.environ.get("CAIC_TEAM_MEMBERS", "").split() if name
    ]

    if not users:
        raise ValueError(
            "No users specified and no CAIC_TEAM_MEMBERS environment variable found"
        )

    month_name = month_names[month]

    print(f"Creating monthly reports for {month_name} {year}")
    print(f"Users: {', '.join(users)}")
    print("Aggregating changelog...")
    data = aggregate_actions(users, month, year)

    print("Creating dataframe...")
    df = pd.DataFrame.from_records(data)
    df = df[df.resource_id != "Test.Fragment"]
    df = df.explode("fields")
    df["fields"] = df["fields"].str.extract(
        f"({'|'.join(include_fields)})", expand=False
    )
    df = df.drop_duplicates()

    df = (
        df.sort_values("action")
        .groupby(["user", "resource_id", "fields"])
        .agg({"action": "/".join})
    )
    df = df.reset_index()

    df["action"] = df.action + " " + df.fields
    df = df.drop("fields", axis=1)
    df = df.groupby(["user", "resource_id"]).agg("; ".join).reset_index()

    df["date"] = f"{year}.{month}"

    df["user"] = df.user.str.extract(f"({'|'.join(users)})", expand=False).str.title()

    print("Fetching bibliography references...")
    ref_data = aggregate_references(df.resource_id.to_list())
    df_ref = pd.DataFrame.from_records(ref_data)
    df = df.merge(df_ref, on="resource_id").fillna("")

    df["reference"] = df[["reference", "pages"]].agg(", ".join, axis=1)

    output_path = os.path.join(os.path.dirname(__file__), "reports")
    os.makedirs(output_path, exist_ok=True)

    print(f"Saving to {output_path}...")
    frames = list(df.groupby("user"))

    for user, frame in frames:
        path = os.path.join(
            output_path, f"{user}_{month_name}_{year}_report.tsv".lower()
        )
        frame["museum_number"] = frame["resource_id"].map(MuseumNumber.of)
        frame = frame.sort_values("museum_number")
        frame = frame.reset_index(drop=True).rename_axis("monthly_index").reset_index()
        frame.monthly_index += 1
        frame = frame[
            ["date", "user", "monthly_index", "resource_id", "reference", "action"]
        ]

        frame.to_csv(path, index=False, header=None, sep="\t")

    if len(frames) != len(users):
        print(f"Warning: expected {len(users)} output files, got {len(frames)}")
        print("Input users were", users)
        print("output users were", [user for user, _ in frames])
