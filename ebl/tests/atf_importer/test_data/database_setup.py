import json
import os
from pathlib import Path
from pymongo import MongoClient


def load_test_signs():
    signs_file = Path(__file__).parent / "signs.json"
    with open(signs_file, "r", encoding="utf-8") as f:
        return json.load(f)


def load_test_words():
    words_file = Path(__file__).parent / "words.json"
    with open(words_file, "r", encoding="utf-8") as f:
        return json.load(f)


def _populate_collection(database, collection_name, data):
    collection = database[collection_name]
    for item in data:
        try:
            collection.update_one({"_id": item["_id"]}, {"$set": item}, upsert=True)
        except Exception as e:
            print(
                f"Warning: Could not insert {collection_name[:-1]} {item['_id']}: {e}"
            )


def populate_signs_for_tests():
    client = MongoClient(os.environ["MONGODB_URI"])
    db_name = os.environ.get("MONGODB_DB")
    database = client.get_database(db_name) if db_name else client.get_database()

    _populate_collection(database, "signs", load_test_signs())
    _populate_collection(database, "words", load_test_words())

    client.close()
