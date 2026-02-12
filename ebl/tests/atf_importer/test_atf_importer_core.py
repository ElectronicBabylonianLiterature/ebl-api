import os
import zipfile
import tempfile
import pytest
from itertools import repeat
from pymongo import MongoClient
from unittest.mock import patch, MagicMock
from ebl.atf_importer.application.atf_importer import AtfImporter
from ebl.tests.factories.fragment import FragmentFactory
from ebl.transliteration.domain.museum_number import MuseumNumber
from ebl.transliteration.domain.text import Text
from ebl.tests.atf_importer.conftest import create_file


def create_cli_argv(tmp_path, author):
    return [
        "atf_importer.py",
        "--input",
        str(tmp_path / "import"),
        "--logdir",
        str(tmp_path / "logs"),
        "--glodir",
        str(tmp_path / "import/glossary"),
        "--author",
        author,
    ]


@pytest.mark.skip(reason="Integration test - skipped by default")
def test_atf_importer(fragment_repository, mock_input):
    client = MongoClient(os.environ["MONGODB_URI"])
    database = client.get_database("ebldev")
    atf_importer = AtfImporter(database, fragment_repository)
    archive = zipfile.ZipFile("ebl/tests/atf_importer/test_data.zip")
    mock_input(repeat(""))
    with tempfile.TemporaryDirectory() as tempdir:
        data_path = f"{tempdir}/test_atf_import_data"
        archive.extractall(data_path)
        for museum_number in [
            "BM.32312",
            "VAT.4956",
            "W.20030.142",
            "VAT.5047",
            "VAT.4936",
            "VAT.4924",
            "BM.47735",
            "BM.34634",
            "BM.34638",
            "BM.47725",
            "BM.34987",
            "BM.45816",
            "BM.35377",
            "BM.46009",
            "BM.35195",
            "BM.32333",
            "BM.34642",
            "BM.45673",
            "BM.34792",
            "BM.36622",
            "BM.35212",
            "BM.33759",
            "BM.36036",
            "BM.32511",
            "BM.35333",
            "BM.37097",
            "BM.36832",
        ]:
            fragment_repository.create(
                FragmentFactory.build(number=MuseumNumber.of(museum_number))
            )
        for dir in os.listdir(data_path):
            glossary_path = f"{data_path}/{dir}"
            atf_dir_path = f"{data_path}/{dir}/00atf"
            logdir_path = f"{data_path}/logs/{dir}"
            atf_importer.run_importer(
                {
                    "input_dir": atf_dir_path,
                    "logdir": logdir_path,
                    "glodir": glossary_path,
                    "author": "Test author",
                }
            )


def test_convert_to_ebl_lines_without_getter(fragment_repository, tmp_path):
    client = MongoClient(os.environ["MONGODB_URI"])
    db_name = os.environ.get("MONGODB_DB")
    database = client.get_database(db_name) if db_name else client.get_database()
    atf_importer = AtfImporter(database, fragment_repository)

    result = atf_importer.convert_to_ebl_lines([], "test.atf")

    assert result == {}


def test_import_into_database_exception_handling(fragment_repository, tmp_path):
    museum_number = "X.99"
    atf = f"&P000099 = {museum_number}\n1'. test line"

    create_file(tmp_path / "import/test.atf", atf)
    create_file(tmp_path / "import/glossary/akk.glo", "")
    create_file(tmp_path / "import/glossary/qpn.glo", "")

    fragment_repository.create(
        FragmentFactory.build(number=MuseumNumber.of(museum_number))
    )

    client = MongoClient(os.environ["MONGODB_URI"])
    db_name = os.environ.get("MONGODB_DB")
    database = client.get_database(db_name) if db_name else client.get_database()
    atf_importer = AtfImporter(database, fragment_repository)

    atf_importer.setup_importer(
        {
            "input_dir": tmp_path / "import",
            "logdir": tmp_path / "logs",
            "glodir": tmp_path / "import/glossary",
            "author": "Test author",
        }
    )

    mock_db_importer = MagicMock()
    mock_db_importer.import_into_database.side_effect = Exception("Test database error")
    atf_importer.database_importer = mock_db_importer

    mock_logger = MagicMock()
    atf_importer.logger = mock_logger

    text = Text(lines=())

    atf_importer.import_into_database(text, [], "test.atf")

    mock_logger.exception.assert_called_once()
    assert "Error while importing into database" in str(mock_logger.exception.call_args)


def test_cli_method(database, fragment_repository, tmp_path):
    museum_number = "X.100"
    atf = f"&P000100 = {museum_number}\n1'. GU₄ 30 ⸢12⸣ [...]"

    create_file(tmp_path / "import/test.atf", atf)
    create_file(tmp_path / "import/glossary/akk.glo", "")
    create_file(tmp_path / "import/glossary/qpn.glo", "")

    fragment_repository.create(
        FragmentFactory.build(number=MuseumNumber.of(museum_number))
    )

    atf_importer = AtfImporter(database, fragment_repository)

    with patch("sys.argv", create_cli_argv(tmp_path, "Test CLI Author")):
        atf_importer.cli()

    fragment = fragment_repository.query_by_museum_number(
        MuseumNumber.of(museum_number)
    )
    assert str(fragment.number) == museum_number


def test_main_method(fragment_repository, tmp_path):
    museum_number = "X.101"
    atf = f"&P000101 = {museum_number}\n1'. GU₄ 30 ⸢12⸣ [...]"

    create_file(tmp_path / "import/test.atf", atf)
    create_file(tmp_path / "import/glossary/akk.glo", "")
    create_file(tmp_path / "import/glossary/qpn.glo", "")

    fragment_repository.create(
        FragmentFactory.build(number=MuseumNumber.of(museum_number))
    )

    with patch("ebl.atf_importer.application.atf_importer.Context") as mock_context:
        mock_context.fragment_repository = fragment_repository

        with patch("sys.argv", create_cli_argv(tmp_path, "Test Main Author")):
            AtfImporter.main()

    fragment = fragment_repository.query_by_museum_number(
        MuseumNumber.of(museum_number)
    )
    assert str(fragment.number) == museum_number
