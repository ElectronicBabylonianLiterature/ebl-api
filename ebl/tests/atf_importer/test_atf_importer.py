import os
import zipfile
import tempfile
import builtins
import pytest
from pymongo import MongoClient
from unittest.mock import patch
from ebl.atf_importer.application.atf_importer import AtfImporter
from ebl.tests.factories.fragment import FragmentFactory, LemmatizedFragmentFactory
from ebl.fragmentarium.domain.fragment_external_numbers import ExternalNumbers
from ebl.transliteration.domain.museum_number import MuseumNumber
from ebl.fragmentarium.domain.joins import Join, Joins
from ebl.fragmentarium.application.joins_schema import JoinSchema
from ebl.tests.atf_importer.test_glossaries_data import GLOSSARY, QPN_GLOSSARY


@pytest.fixture(autouse=True)
def patched_fragment_updater(fragment_updater):
    with patch(
        "ebl.context.Context.get_fragment_updater",
        return_value=fragment_updater,
    ):
        yield


def create_file(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.touch()
    path.write_text(content)


def setup_and_run_importer(
    atf_string, tmp_path, database, fragment_repository, glossary="", qpn_glossary=""
):
    atf_importer = AtfImporter(database, fragment_repository)
    create_file(tmp_path / "import/test.atf", atf_string)
    create_file(tmp_path / "import/glossary/akk.glo", glossary)
    create_file(tmp_path / "import/glossary/qpn.glo", qpn_glossary)
    atf_importer.run_importer(
        {
            "input_dir": tmp_path / "import",
            "logdir": tmp_path / "logs",
            "glodir": tmp_path / "import/glossary",
            "author": "Test author",
        }
    )


def check_importing_and_logs(museum_number, fragment_repository, tmp_path):
    fragment = fragment_repository.query_by_museum_number(
        MuseumNumber.of(museum_number)
    )
    assert str(fragment.number) == museum_number
    check_logs(tmp_path, museum_number)


def check_logs(tmp_path, museum_number):
    for log_file in os.listdir(tmp_path / "logs"):
        with open(tmp_path / f"logs/{log_file}") as logfile:
            if log_file == "imported_files.txt":
                assert (
                    f"test.atf successfully imported as {museum_number}"
                    in logfile.read()
                )
            else:
                assert logfile.read() == ""


@pytest.fixture
def mock_input(monkeypatch):
    def _set_input_responses(responses):
        responses_iter = iter(responses)
        monkeypatch.setattr(builtins, "input", lambda *args: next(responses_iter))
        return responses_iter

    return _set_input_responses


def test_logger_writes_files(database, fragment_repository, tmp_path):
    museum_number = "BM.1"
    atf = f"&P000001 = {museum_number}\n1'. GU₄ 30 ⸢12⸣ [...]"
    fragment_repository.create(FragmentFactory.build(number=MuseumNumber.of("BM.1")))
    setup_and_run_importer(atf, tmp_path, database, fragment_repository)
    assert os.listdir(tmp_path / "logs") == [
        "imported_files.txt",
        "not_imported_files.txt",
        "error_lines.txt",
        "not_lemmatized_tokens.txt",
        "unparsable_lines.txt",
    ]
    check_importing_and_logs(museum_number, fragment_repository, tmp_path)


def test_find_museum_number_by_cdli_number(database, fragment_repository, tmp_path):
    museum_number = "BM.123"
    atf = "&P111111 = XXX\n1'. GU₄ 30 ⸢12⸣ [...]"
    fragment_repository.create(
        FragmentFactory.build(
            number=MuseumNumber.of(museum_number),
            external_numbers=ExternalNumbers(cdli_number="P111111"),
        )
    )
    setup_and_run_importer(atf, tmp_path, database, fragment_repository)
    check_importing_and_logs(museum_number, fragment_repository, tmp_path)


def test_find_museum_number_by_traditional_reference(
    database, fragment_repository, tmp_path
):
    museum_number = "BM.222"
    test_id = "test reference"
    atf = f"&P000001 = {test_id}\n1. GU₄ 30 ⸢12⸣ [...]"
    fragment_repository.create(
        FragmentFactory.build(
            number=MuseumNumber.of(museum_number), traditional_references=[test_id]
        )
    )
    setup_and_run_importer(atf, tmp_path, database, fragment_repository)
    check_importing_and_logs(museum_number, fragment_repository, tmp_path)


def test_museum_number_input_by_user(
    database, fragment_repository, tmp_path, mock_input
):
    museum_number = "BM.2"
    test_id = "test reference"
    atf = f"&P000001 = {test_id}\n1. GU₄ 30 ⸢12⸣ [...]"
    fragment_repository.create(FragmentFactory.build(number=MuseumNumber.of("BM.2")))
    responses = mock_input([museum_number, "end"])
    setup_and_run_importer(atf, tmp_path, database, fragment_repository)
    assert next(responses) == "end"
    check_importing_and_logs(museum_number, fragment_repository, tmp_path)


def test_museum_number_skip_by_user(
    database, fragment_repository, tmp_path, mock_input
):
    responses = mock_input(["skip", "end"])
    atf = "&P000001 = test reference\n1. GU₄ 30 ⸢12⸣ [...]"
    setup_and_run_importer(atf, tmp_path, database, fragment_repository)
    assert next(responses) == "end"
    for log_file in os.listdir(tmp_path / "logs"):
        with open(tmp_path / f"logs/{log_file}") as logfile:
            if log_file == "not_imported_files.txt":
                assert (
                    "test.atf could not be imported: Museum number not found"
                    in logfile.read()
                )
            else:
                assert logfile.read() == ""


def test_ask_overwrite_existing_edition(
    database, fragment_repository, tmp_path, mock_input
):
    museum_number = "N.1"
    atf = f"&P000001 = {museum_number}\n1. GU₄ 30 ⸢12⸣ [...]"
    responses = mock_input(["Y", "end"])
    fragment_repository.create(
        LemmatizedFragmentFactory.build(number=MuseumNumber.of(museum_number))
    )
    setup_and_run_importer(atf, tmp_path, database, fragment_repository)
    assert next(responses) == "end"
    check_importing_and_logs(museum_number, fragment_repository, tmp_path)


def test_ask_overwrite_existing_edition_cancel(
    database, fragment_repository, tmp_path, mock_input
):
    museum_number = "N.1"
    atf = f"&P000001 = {museum_number}\n1. GU₄ 30 ⸢12⸣ [...]"
    responses = mock_input(["N", "end"])
    fragment_repository.create(
        LemmatizedFragmentFactory.build(number=MuseumNumber.of(museum_number))
    )
    setup_and_run_importer(atf, tmp_path, database, fragment_repository)
    assert next(responses) == "end"
    with open(tmp_path / "logs/not_imported_files.txt") as logfile:
        assert (
            "test.atf could not be imported: Edition found, importing cancelled by user"
            in logfile.read()
        )


def test_import_fragment_to_lowest_join(
    database, fragment_repository, tmp_path, mock_input
):
    museum_number_join_low = "X.1"
    museum_number_join_high = "X.2"
    atf = f"&P000001 = {museum_number_join_high}\n1. LUGAL [x]"
    for number_1, number_2 in [
        (museum_number_join_low, museum_number_join_high),
        (museum_number_join_high, museum_number_join_low),
    ]:
        fragment = FragmentFactory.build(
            number=MuseumNumber.of(number_1),
            joins=Joins(
                ((Join(MuseumNumber.of(number_2), is_in_fragmentarium=True),),),
            ),
        )
        fragment_repository.create(fragment)

    database["joins"].insert_one(
        {
            "fragments": [
                {
                    **JoinSchema(exclude=["is_in_fragmentarium"]).dump(
                        Join(MuseumNumber.of(museum_number))
                    ),
                    "group": index,
                }
                for index, museum_number in enumerate(
                    [museum_number_join_low, museum_number_join_high]
                )
            ]
        }
    )
    setup_and_run_importer(atf, tmp_path, database, fragment_repository)
    check_importing_and_logs(museum_number_join_low, fragment_repository, tmp_path)


def test_import_fragment_correct_parsing_errors(
    database, fragment_repository, tmp_path, mock_input, capsys
):
    museum_number = "H.2"
    atf = f"&P000001 = {museum_number}\n1. GGG"
    responses = mock_input(["1. GA", "end"])
    fragment_repository.create(
        FragmentFactory.build(number=MuseumNumber.of(museum_number))
    )
    setup_and_run_importer(atf, tmp_path, database, fragment_repository)
    captured = capsys.readouterr()
    expected = "Error: Invalid transliteration \nThe following text line cannot be parsed:\n1. GGG\nPlease input the corrected line, then press enter:\n"
    assert captured.out == expected
    assert next(responses) == "end"
    check_importing_and_logs(museum_number, fragment_repository, tmp_path)


# ToDo: Add tests for:
# - importing multiple files
# - lemmatization: missing words, multiple options,


def test_lemmatization(fragment_repository, tmp_path):
    client = MongoClient(os.environ["MONGODB_URI"])
    database = client.get_database(os.environ.get("MONGODB_DB"))
    museum_number = "BM.1"
    fragment_repository.create(
        FragmentFactory.build(number=MuseumNumber.of(museum_number))
    )
    atf = (
        f"&P000001 = {museum_number}\n"
        "64. * ina {iti}ZIZ₂ U₄ 14.KAM [AN.KU₁₀] 30 GAR-ma <<ina>> KAN₅-su KU₄ DINGIR GU₇\n"
        "#lem: šumma[if]CNJ; ina[in]PRP; Šabāṭu[Month XI]MN; ūmu[day]N; n; antallû[eclipse]N; Sîn["
        "moon]N; šakānu[take place]V; adru[dark]AV; erēbu[enter]V; ilu["
        "god]N; akālu[eat]V"
    )

    setup_and_run_importer(
        atf, tmp_path, database, fragment_repository, GLOSSARY, QPN_GLOSSARY
    )
    check_importing_and_logs(museum_number, fragment_repository, tmp_path)
    fragment = fragment_repository.query_by_museum_number(
        MuseumNumber.of(museum_number)
    )
    lemmatization = [word.unique_lemma for word in fragment.text.lines[0]._content]
    assert lemmatization == [
        ("šumma I",),
        ("ina I",),
        ("Šabāṭu I",),
        ("ūmu I",),
        (),
        ("antalû I",),
        ("Sîn I",),
        ("šakānu I",),
        (),
        ("adru I",),
        ("erēbu I",),
        ("ilu I",),
        ("akālu I",),
    ]


def test_lemmatization_with_omission(fragment_repository, tmp_path):
    client = MongoClient(os.environ["MONGODB_URI"])
    database = client.get_database(os.environ.get("MONGODB_DB"))
    museum_number = "BM.1"
    fragment_repository.create(
        FragmentFactory.build(number=MuseumNumber.of(museum_number))
    )
    atf = (
        f"&P000001 = {museum_number}\n"
        "64. * <<ina>> ina <<{iti}ZIZ₂ A U₄>> {<<iti>>.iti}<<A>>.ZIZ₂.<<A>> U₄ 14.KAM\n"
        "#lem: šumma[if]CNJ; ina[in]PRP; Šabāṭu[Month XI]MN; ūmu[day]N; n"
    )
    setup_and_run_importer(
        atf, tmp_path, database, fragment_repository, GLOSSARY, QPN_GLOSSARY
    )
    check_importing_and_logs(museum_number, fragment_repository, tmp_path)
    fragment = fragment_repository.query_by_museum_number(
        MuseumNumber.of(museum_number)
    )
    lemmatization = [word.unique_lemma for word in fragment.text.lines[0]._content]
    assert lemmatization == [
        ("šumma I",),
        (),
        ("ina I",),
        (),
        (),
        (),
        ("Šabāṭu I",),
        ("ūmu I",),
        (),
    ]


# @pytest.mark.skip(reason="heavy test")
def test_atf_importer(fragment_repository):
    client = MongoClient(os.environ["MONGODB_URI"])
    database = client.get_database(os.environ.get("MONGODB_DB"))
    atf_importer = AtfImporter(database, fragment_repository)
    archive = zipfile.ZipFile(
        "ebl/tests/atf_importer/test_data.zip"
    )  # ToDo: Check `test_data2`
    with tempfile.TemporaryDirectory() as tempdir:
        data_path = f"{tempdir}/test_atf_import_data"
        archive.extractall(data_path)
        for dir in os.listdir(data_path):
            glossary_path = f"{data_path}/{dir}"  # f"{data_path}"
            atf_dir_path = f"{data_path}/{dir}/00atf"  # f"{data_path}"
            logdir_path = f"{data_path}/logs/{dir}"
            print(f"Testing import of atf data in {atf_dir_path}")
            # print("Running", " ".join(command))
            atf_importer.run_importer(
                {
                    "input_dir": atf_dir_path,
                    "logdir": logdir_path,
                    "glodir": glossary_path,
                    "author": "Test author",
                }
            )


"""
def test_atf_importer(database, fragment_repository):
    # Test bulk import.
    # importer_path = "ebl/atf_importer/application/atf_importer.py"
    atf_importer = AtfImporter(database)
    archive = zipfile.ZipFile("ebl/tests/atf_importer/test_data.zip")
    with tempfile.TemporaryDirectory() as tempdir:
        data_path = f"{tempdir}/test_atf_import_data"
        archive.extractall(data_path)
        for dir in os.listdir(data_path):
            glossary_akk_path = f"{data_path}/{dir}/akk.glo"
            # glossary_qpn_path = f"{data_path}/{dir}/qpn.glo"
            atf_dir_path = f"{data_path}/{dir}/00atf"
            logdir_path = f"{data_path}/logs/{dir}"
            print(f"Testing import of atf data in {atf_dir_path}")
            # print("Running", " ".join(command))
            atf_importer.run_importer(
                {
                    "input_dir": atf_dir_path,
                    "logdir": logdir_path,
                    "glodir": glossary_akk_path,
                    "author": "Test author",
                }
            )

            '''
            command = [
                "python",
                "run",
                importer_path,
                "-i",
                atf_dir_path,
                "-l",
                logdir_path,
                "-g",
                glossary_akk_path,
                "-a",
                "Test author",
            ]
            '''

            # result = subprocess.run(
            #    command,
            #    shell=True,
            #    capture_output=True,
            # )
            # print(result.stdout)
            # self.assertIn("expected out", result.stdout)
            # filenames = [
            #    filename for filename in os.listdir(atf_path) if ".atf" in filename
            # ]
            # for filename in filenames:
            #    print(f"{atf_path}/{filename}")
"""
