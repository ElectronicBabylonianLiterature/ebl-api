import os
import uuid

import pytest
from pymongo import MongoClient


def pytest_configure(config):
    temp_db_name = f"ebltest_{uuid.uuid4().hex[:8]}"

    config._original_mongodb_db = os.environ.get("MONGODB_DB")
    config._temp_db_name = temp_db_name

    if os.getenv("CI") == "true":
        os.environ["MONGODB_DB"] = temp_db_name
    else:
        from pymongo_inmemory import MongoClient as InMemoryMongoClient

        client = InMemoryMongoClient()
        config._original_mongodb_uri = os.environ.get("MONGODB_URI")
        os.environ["MONGODB_URI"] = f"mongodb://{client.HOST}:{client.PORT}"
        os.environ["MONGODB_DB"] = temp_db_name
        config._inmemory_client = client

    from ebl.tests.atf_importer.test_data.database_setup import populate_signs_for_tests

    populate_signs_for_tests()


@pytest.fixture(scope="function")
def database():
    client = MongoClient(os.environ["MONGODB_URI"])
    db_name = os.environ.get("MONGODB_DB")
    db = client.get_database(db_name) if db_name else client.get_database()

    for collection_name in db.list_collection_names():
        if collection_name not in ["signs", "words"]:
            db[collection_name].delete_many({})

    return db


def pytest_unconfigure(config):
    if hasattr(config, "_temp_db_name"):
        from pymongo import MongoClient

        mongodb_uri = os.environ.get("MONGODB_URI", "mongodb://localhost:27017")
        client = MongoClient(mongodb_uri)
        client.drop_database(config._temp_db_name)
        client.close()

    if hasattr(config, "_original_mongodb_db"):
        if config._original_mongodb_db is not None:
            os.environ["MONGODB_DB"] = config._original_mongodb_db
        elif "MONGODB_DB" in os.environ:
            del os.environ["MONGODB_DB"]

    if hasattr(config, "_original_mongodb_uri"):
        if config._original_mongodb_uri is not None:
            os.environ["MONGODB_URI"] = config._original_mongodb_uri
        elif "MONGODB_URI" in os.environ:
            del os.environ["MONGODB_URI"]
