from pymongo import MongoClient
from ebl.mongo_collection import MongoCollection
import os
import sys
import json
from pprint import pprint

ANNOTATIONS_COLLECTION = "annotations"

client = MongoClient(os.environ["MONGODB_URI"])
DB = os.environ.get("MONGODB_DB")
database = client.get_database(DB)
annotations = MongoCollection(database, ANNOTATIONS_COLLECTION)


if __name__ == "__main__":
    print("\nCreate full Script entry for all CroppedSigns\n")
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

    result = annotations.update_many(
        {},
        [
            {
                "$set": {
                    "annotations": {
                        "$map": {
                            "input": "$annotations",
                            "as": "annotation",
                            "in": {
                                "geometry": "$$annotation.geometry",
                                "data": "$$annotation.data",
                                "croppedSign": {
                                    "imageId": "$$annotation.croppedSign.imageId",
                                    "script": {
                                        "$switch": {
                                            "branches": [
                                                {
                                                    "case": {
                                                        "$eq": [
                                                            "$$annotation.croppedSign.script",
                                                            key,
                                                        ]
                                                    },
                                                    "then": {
                                                        "period": value["period"],
                                                        "periodModifier": value[
                                                            "period_modifier"
                                                        ],
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
                                    },
                                    "label": "$$annotation.croppedSign.label",
                                },
                            },
                        }
                    }
                }
            }
        ],
    )

    pprint(result.raw_result)
