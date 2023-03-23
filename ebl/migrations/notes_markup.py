from pymongo import MongoClient
from ebl.mongo_collection import MongoCollection
from ebl.transliteration.infrastructure.collections import FRAGMENTS_COLLECTION
from ebl.fragmentarium.domain.fragment import parse_markup_with_paragraphs
import os
import sys
from pprint import pprint
import pandas as pd


client = MongoClient(os.environ["MONGODB_URI"])
DB = "ebl"
database = client.get_database(DB)
fragments = MongoCollection(database, FRAGMENTS_COLLECTION)

if __name__ == "__main__":
    print("\nParse the notes field of all fragments\n")
    print("This migration applies to the db", repr(DB))
    if DB == "ebl":
        print("WARNING: THIS IS THE PRODUCTION DB.")
    prompt = input("Continue? (y/n) ")

    if prompt != "y":
        print("Aborting.")
        sys.exit()

    # 1. create notes2: {text: $notes, parts: []} in mongo:
    # db.getCollection('fragments')
    #     .updateMany(
    #         {},
    #         [
    #         {"$set": {
    #             "notes2": {
    #             "text": "$notes",
    #             "parts": []
    #             }
    #         }}
    #         ]
    #     );
    # 2. parse those documents that have something in $notes and update notes2.parts with dumped markup parts
    # 3. Remove notes and rename notes2 -> notes

    parsed_notes = []
    failed = []

    query = {"notes": {"$exists": True, "$ne": ""}}
    total = fragments.count_documents(query)

    for i, fragment in enumerate(
        fragments.find_many(query, projection={"text": "$notes"}), start=1
    ):
        print(f"Parsing {i} of {total} ({100*i/total:.2f}%)\r", end="")

        id_ = fragment["_id"]

        try:
            parts = parse_markup_with_paragraphs(fragment["text"])
            parsed_notes.append((id_, parts))
        except Exception as error:
            parsed_notes.append((id_, []))
            failed.append({**fragment, "error": error})
    
    print()
    print(len(failed), "failed, see failed_note_parses.csv")
    
    df = pd.DataFrame.from_records(failed)
    df.to_csv("failed_note_parses.csv", index=False)

    # print("Applying the migration (this may take a while)...")
    # result = fragments.update_many({}, [{"$set": {"legacyScript": "$script"}}])
    # print("Process finished. Result:")
    # pprint(result.raw_result)
