from pymongo import MongoClient
from ebl.mongo_collection import MongoCollection
from ebl.transliteration.infrastructure.collections import FRAGMENTS_COLLECTION
import os
import sys
import json
from pprint import pprint

client = MongoClient(os.environ["MONGODB_URI"])
DB = os.environ.get("MONGODB_DB")
database = client.get_database(DB)
fragments = MongoCollection(database, FRAGMENTS_COLLECTION)


if __name__ == "__main__":
    print(
        "\nMap the 'legacyScript' value in each fragment "
        "to its corresponding full Script entry\n"
    )
    print("This migration applies to the db", repr(DB))

    if DB == "ebl":
        print("WARNING: THIS IS THE PRODUCTION DB.")
    prompt = input("Continue? (y/n) ")

    if prompt != "y":
        print("Aborting.")
        sys.exit()

    print("Applying the migration (this may take a while)...")

    with open("ebl/migrations/mapping.json") as jf:
        mapping = json.load(jf)

    result = fragments.update_many(
        {},
        [
            {
                "$set": {
                    "script": {
                        "$switch": {
                            "branches": [
                                {
                                    "case": {"$eq": ["$legacyScript", key]},
                                    "then": {
                                        "period": value["period"],
                                        "periodModifier": value["period_modifier"],
                                        "uncertain": value["uncertain"],
                                    },
                                }
                                for key, value in mapping.items()
                            ],
                            "default": {
                                "period": "None",
                                "periodModifier": "None",
                                "uncertain": False,
                            },
                        }
                    }
                }
            }
        ],
    )

    pprint(result.raw_result)
