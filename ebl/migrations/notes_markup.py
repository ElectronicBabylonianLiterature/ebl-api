from pymongo import MongoClient
from ebl.mongo_collection import MongoCollection
from ebl.transliteration.infrastructure.collections import FRAGMENTS_COLLECTION
from ebl.fragmentarium.domain.fragment import parse_markup_with_paragraphs
from ebl.fragmentarium.application.fragment_schema import NotesSchema
import os
import sys
import pandas as pd
import numpy as np
import re


client = MongoClient(os.environ["MONGODB_URI"])
DB = "ebldev"
database = client.get_database(DB)
fragments = MongoCollection(database, FRAGMENTS_COLLECTION)


def normalize_newlines(text):
    return re.sub("\n+", "\n\n", text.strip())


if __name__ == "__main__":
    print("\nParse the notes field of all fragments\n")
    print("This migration applies to the db", repr(DB))
    if DB == "ebl":
        print("!!! WARNING: THIS IS THE PRODUCTION DB. !!!")
        print("Only proceed after creating a backup duplicate of the fragment collection.")
    prompt = input("Continue? (y/n) ")

    if prompt != "y":
        print("Aborting.")
        sys.exit()

    parsed_notes = []
    failed = []

    query = {"notes": {"$exists": True, "$ne": ""}}
    total = fragments.count_documents(query)

    df = pd.read_csv("failed_note_parses_fixed.csv")
    df["text"] = df.text.str.strip().replace("", np.nan)
    df = df[~df.text.isna()]
    mapping = dict(zip(df["_id"], df.text))

    for i, fragment in enumerate(
        fragments.find_many(query, projection={"text": "$notes"}), start=1
    ):
        print(f"Parsing {i} of {total} ({100*i/total:.2f}%)\r", end="")

        id_ = fragment["_id"]
        text = normalize_newlines(mapping.get(id_, fragment["text"]))

        try:
            parts = parse_markup_with_paragraphs(text)
            parsed_notes.append((id_, text, parts))
        except Exception as error:
            parsed_notes.append((id_, "", []))
            failed.append({**fragment, "error": error})

    print()

    fails = len(failed)

    if fails > 0:
        print(fails, "failed -- aborting update. See failed_note_parses.csv")
        df2 = pd.DataFrame.from_records(failed)
        df2.to_csv("failed_note_parses.csv", index=False)
    else:
        print(fails, "fails -- continuing with update. This may take a while.")
        print("Updating db")

        total = len(parsed_notes)

        for i, (id_, text, parts) in enumerate(parsed_notes, start=1):
            print(f"Updating {i} of {total} ({100*i/total:.2f}%)\r", end="")
            notes = NotesSchema().dump({"text": text, "parts": parts})
            fragments.update_one({"_id": id_}, {"$set": {"notesParsed": notes}})

    # print("Applying the migration (this may take a while)...")
    # result = fragments.update_many({}, [{"$set": {"legacyScript": "$script"}}])
    # print("Process finished. Result:")
    # pprint(result.raw_result)
