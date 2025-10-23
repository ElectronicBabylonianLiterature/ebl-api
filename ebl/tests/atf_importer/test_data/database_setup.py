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


def populate_database_for_tests(temp_db_name):
    if temp_db_name in ["ebl", "ebldev"]:
        raise RuntimeError(
            f"CRITICAL SAFETY ERROR: Attempted to populate production database '{temp_db_name}'. "
            "Tests must only use isolated test databases."
        )
    if not temp_db_name.startswith("ebltest_"):
        raise RuntimeError(
            f"CRITICAL SAFETY ERROR: Test database name '{temp_db_name}' does not start with 'ebltest_'. "
            "All test databases must follow the naming convention 'ebltest_*'."
        )
    client = MongoClient(os.environ["MONGODB_URI"])
    database = client.get_database(temp_db_name)

    _populate_collection(database, "signs", load_test_signs())
    _populate_collection(database, "words", load_test_words())

    client.close()
