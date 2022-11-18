from pymongo import MongoClient
from ebl.mongo_collection import MongoCollection
from ebl.transliteration.infrastructure.collections import FRAGMENTS_COLLECTION
import os
import sys
from pprint import pprint


client = MongoClient(os.environ["MONGODB_URI"])
DB = os.environ.get("MONGODB_DB")
database = client.get_database(DB)
fragments = MongoCollection(database, FRAGMENTS_COLLECTION)

if __name__ == "__main__":
    print(
        "\nCreate a new field 'legacyScript' with the content of 'script' in each fragment\n"
    )
    print("This migration applies to the db", repr(DB))
    if DB == "ebl":
        print("WARNING: THIS IS THE PRODUCTION DB.")
    prompt = input("Continue? (y/n) ")

    if prompt != "y":
        print("Aborting.")
        sys.exit()

    print("Applying the migration (this may take a while)...")
    result = fragments.update_many({}, [{"$set": {"legacyScript": "$script"}}])
    print("Process finished. Result:")
    pprint(result.raw_result)
