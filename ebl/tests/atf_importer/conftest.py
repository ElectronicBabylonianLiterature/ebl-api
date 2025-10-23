import os
import uuid
import builtins

import pytest
from pymongo import MongoClient
from unittest.mock import patch
from ebl.atf_importer.application.atf_importer import AtfImporter
from ebl.transliteration.domain.museum_number import MuseumNumber
from ebl.transliteration.domain.text import TextLine
from ebl.tests.atf_importer.test_data.database_setup import populate_database_for_tests


def pytest_configure(config):
    temp_db_name = f"ebltest_{uuid.uuid4().hex[:8]}"
    production_dbs = ["ebl", "ebldev"]
    current_db = os.environ.get("MONGODB_DB")
    if current_db in production_dbs:
        raise RuntimeError(
            f"CRITICAL SAFETY ERROR: Cannot run tests with MONGODB_DB='{current_db}'. "
            f"Production databases {production_dbs} must NEVER be used in tests. "
            "Unset MONGODB_DB and MONGODB_URI before running tests."
        )
    config._original_mongodb_db = os.environ.get("MONGODB_DB")
    config._original_mongodb_uri = os.environ.get("MONGODB_URI")
    config._temp_db_name = temp_db_name
    from pymongo_inmemory import MongoClient as InMemoryMongoClient

    client = InMemoryMongoClient()
    os.environ["MONGODB_URI"] = f"mongodb://{client.HOST}:{client.PORT}"
    os.environ["MONGODB_DB"] = temp_db_name
    config._inmemory_client = client
    if os.environ["MONGODB_DB"] in production_dbs:
        raise RuntimeError(
            "CRITICAL SAFETY ERROR: MONGODB_DB is set to production database. "
            "This should never happen. Tests aborted."
        )
    populate_database_for_tests(temp_db_name)


@pytest.fixture(scope="function")
def database():
    db_name = os.environ.get("MONGODB_DB")
    production_dbs = ["ebl", "ebldev"]
    if db_name in production_dbs:
        raise RuntimeError(
            f"CRITICAL SAFETY ERROR: Cannot use production database '{db_name}' in tests. "
            "Tests must use isolated test databases only."
        )
    client = MongoClient(os.environ["MONGODB_URI"])
    db = client.get_database(db_name) if db_name else client.get_database()
    for collection_name in db.list_collection_names():
        if collection_name not in ["signs", "words"]:
            db[collection_name].delete_many({})
    return db


def pytest_unconfigure(config):
    if hasattr(config, "_temp_db_name"):
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


@pytest.fixture(autouse=True)
def patched_fragment_updater(fragment_updater):
    with patch(
        "ebl.context.Context.get_fragment_updater",
        return_value=fragment_updater,
    ):
        yield


@pytest.fixture
def mock_input(monkeypatch):
    def _set_input_responses(responses):
        responses_iter = iter(responses)
        monkeypatch.setattr(builtins, "input", lambda *args: next(responses_iter))
        return responses_iter

    return _set_input_responses


def create_file(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.touch()
    path.write_text(content)


def setup_and_run_importer(
    atf_string,
    tmp_path,
    fragment_repository,
    glossaries=None,
):
    if not glossaries:
        glossaries = {"akk": "", "qpn": ""}
    create_file(tmp_path / "import/test.atf", atf_string)
    for key in glossaries.keys():
        create_file(tmp_path / f"import/glossary/{key}.glo", glossaries[key])
    client = MongoClient(os.environ["MONGODB_URI"])
    db_name = os.environ.get("MONGODB_DB")
    database = client.get_database(db_name) if db_name else client.get_database()

    atf_importer = AtfImporter(database, fragment_repository)
    atf_importer.run_importer(
        {
            "input_dir": tmp_path / "import",
            "logdir": tmp_path / "logs",
            "glodir": tmp_path / "import/glossary",
            "author": "Test author",
        }
    )


def check_importing_and_logs(museum_number, fragment_repository, tmp_path, logs=None):
    if logs is None:
        logs = {}
    fragment = fragment_repository.query_by_museum_number(
        MuseumNumber.of(museum_number)
    )
    assert str(fragment.number) == museum_number
    check_logs(tmp_path, museum_number, logs)


def check_logs(tmp_path, museum_number, logs):
    for log_filename in os.listdir(tmp_path / "logs"):
        with open(tmp_path / f"logs/{log_filename}") as logfile:
            logfile_content = logfile.read()
            if log_filename in logs.keys():
                check_custom_logs_content(logs, log_filename, logfile_content)
            elif log_filename == "imported_files.txt":
                assert (
                    f"test.atf successfully imported as {museum_number}"
                    in logfile_content
                )
            else:
                assert logfile_content == ""


def check_custom_logs_content(logs, log_filename, logfile_content):
    if logs[log_filename]:
        for log_segment in logs[log_filename]:
            if len(log_segment) > 0:
                assert log_segment in logfile_content
            else:
                assert log_segment == logfile_content


def check_lemmatization(fragment_repository, museum_number, expected_lemmatization):
    fragment = fragment_repository.query_by_museum_number(
        MuseumNumber.of(museum_number)
    )
    text_lines = [line for line in fragment.text.lines if isinstance(line, TextLine)]
    lemmatization = [word.unique_lemma for word in text_lines[0]._content]
    assert lemmatization == expected_lemmatization
