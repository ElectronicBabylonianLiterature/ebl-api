from pymongo import MongoClient
from ebl.mongo_collection import MongoCollection
from ebl.transliteration.infrastructure.collections import FRAGMENTS_COLLECTION
import os
import sys
import json


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

    with open("ebl/migrations/script_mapping.json") as jf:
        mapping = json.load(jf)

    for fragment in fragments.aggregate([{"$project": {"legacyScript": 1}}]):
        script = fragment["legacyScript"].replace("\x0b", "")
        if script in mapping:
            value = mapping[script]
            fragments.update_one(
                {"_id": fragment["_id"]},
                {
                    "$set": {
                        "script": {
                            "period": value["long_name"],
                            "periodModifier": value["period_modifier"],
                            "uncertain": value["uncertain"],
                        }
                    }
                },
            )

    print("Process finished.")
