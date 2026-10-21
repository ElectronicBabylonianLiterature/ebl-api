import csv
import json
import runpy

import pytest
from marshmallow import ValidationError

from ebl.io.fragments import importer_cli
from ebl.io.fragments.importer_cli import build_parser, load_fragments, run
from ebl.tests.transliteration.storage_test_helpers import has_key

COLLECTION = "fragments"


@pytest.fixture
def importable(valid_fragment_data, fragment) -> dict:
    return {**valid_fragment_data, "_id": str(fragment.number)}


@pytest.fixture
def in_tmp_path(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    return tmp_path


def write_json(directory, name: str, data) -> str:
    path = directory / name
    path.write_text(json.dumps(data))
    return str(path)


def read_tsv(path) -> list:
    with open(path, newline="") as tsv_file:
        return list(csv.reader(tsv_file, delimiter="\t"))


def run_cli(argv, database, read_input=input) -> None:
    run(build_parser().parse_args(argv), database, read_input)


@pytest.mark.parametrize(
    "argv,subcommand,database,strict",
    [
        (["import", "a.json"], "import", "ebldev", False),
        (["validate", "a.json", "--strict", "-db", "ebl"], "validate", "ebl", True),
        (["reindex"], "reindex", "ebldev", None),
    ],
)
def test_build_parser(argv, subcommand, database, strict):
    args = build_parser().parse_args(argv)

    assert (args.subcommand, args.database) == (subcommand, database)
    assert getattr(args, "strict", None) == strict


def test_load_fragments_of_a_collection_file(in_tmp_path, importable):
    path = write_json(in_tmp_path, "collection.json", [importable])

    assert load_fragments([path]) == ({f"{path}[0]": importable}, True)


def test_load_fragments_falls_back_to_a_single_document(in_tmp_path, importable):
    path = write_json(in_tmp_path, "document.json", importable)

    assert load_fragments([path]) == ({path: importable}, False)


def test_load_fragments_of_several_files(in_tmp_path, importable):
    paths = [write_json(in_tmp_path, f"{name}.json", importable) for name in "ab"]

    assert load_fragments(paths) == (dict.fromkeys(paths, importable), False)


def test_import_writes_sparse_fragments_and_a_summary(
    in_tmp_path, database, seeded_provenance_service, importable
):
    path = write_json(in_tmp_path, "document.json", importable)

    run_cli(["import", path], database)

    stored = database[COLLECTION].find_one({"_id": importable["_id"]})
    assert not has_key(stored["text"], "erasure")
    assert "_sortKey" in stored
    [summary] = in_tmp_path.glob("fragment_import_summary_*.tsv")
    assert read_tsv(summary) == [["id", "file"], [importable["_id"], path]]


def test_validate_reports_invalid_documents_without_writing(
    in_tmp_path, database, seeded_provenance_service, importable, capsys
):
    valid = write_json(in_tmp_path, "valid.json", importable)
    invalid = write_json(in_tmp_path, "invalid.json", {"_id": "not a number"})

    run_cli(["validate", valid, invalid], database)

    assert database[COLLECTION].count_documents({}) == 0
    assert [row[0] for row in read_tsv(in_tmp_path / "invalid_texts.tsv")] == [
        "file",
        invalid,
    ]
    assert "Validation of 1 out of 2 document(s) successful." in capsys.readouterr().out


def test_strict_import_aborts_on_an_invalid_document(
    in_tmp_path, database, seeded_provenance_service
):
    path = write_json(in_tmp_path, "invalid.json", {"_id": "not a number"})

    with pytest.raises(ValidationError):
        run_cli(["import", path, "--strict"], database)


def test_import_without_valid_documents_writes_nothing(
    in_tmp_path, database, seeded_provenance_service, importable, capsys
):
    database[COLLECTION].insert_one(importable)
    path = write_json(in_tmp_path, "duplicate.json", importable)

    run_cli(["import", path], database)

    assert database[COLLECTION].count_documents({}) == 1
    assert "No data to import." in capsys.readouterr().out


def test_import_without_json_files_finds_nothing(in_tmp_path, database, capsys):
    run_cli(["import", "notes.txt"], database)

    assert "No fragments found." in capsys.readouterr().out


def test_production_import_aborts_without_the_passphrase(
    in_tmp_path, database, seeded_provenance_service, importable
):
    path = write_json(in_tmp_path, "document.json", importable)

    with pytest.raises(SystemExit, match="Aborting."):
        run_cli(["import", path, "-db", "ebl"], database, lambda prompt: "no")

    assert database[COLLECTION].count_documents({}) == 0


def test_production_import_proceeds_with_the_passphrase(
    in_tmp_path, database, seeded_provenance_service, importable
):
    path = write_json(in_tmp_path, "document.json", importable)

    run_cli(["import", path, "-db", "ebl"], database, lambda prompt: "HAMMURABI")

    assert database[COLLECTION].count_documents({}) == 1


def test_reindex_sets_sort_keys(database, importable, capsys):
    database[COLLECTION].insert_one(importable)

    run_cli(["reindex"], database)

    assert database[COLLECTION].find_one({})["_sortKey"] == 0
    assert "Sort index built successfully." in capsys.readouterr().out


def test_main_connects_to_the_selected_database(monkeypatch, database):
    connected = []
    monkeypatch.setenv("MONGODB_URI", "mongodb://example.invalid")
    monkeypatch.setattr(
        importer_cli,
        "MongoClient",
        lambda uri: connected.append(uri) or database.client,
    )
    monkeypatch.setattr(
        importer_cli, "run", lambda args, target: connected.append(target.name)
    )

    importer_cli.main(["reindex"])

    assert connected == ["mongodb://example.invalid", "ebldev"]


def test_running_the_importer_module_calls_main(monkeypatch):
    calls = []
    monkeypatch.setattr(importer_cli, "main", lambda: calls.append("main"))

    runpy.run_module("ebl.io.fragments.importer", run_name="__main__")

    assert calls == ["main"]
