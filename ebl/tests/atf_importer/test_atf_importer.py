import os
import zipfile
import tempfile
import builtins
import pytest
from pymongo import MongoClient
from unittest.mock import patch
from ebl.atf_importer.application.atf_importer import AtfImporter

# from ebl.atf_importer.domain.legacy_atf_converter import LegacyAtfConverter
# from ebl.atf_importer.application.lines_getter import EblLinesGetter
from ebl.tests.factories.fragment import FragmentFactory
from ebl.fragmentarium.domain.fragment_external_numbers import ExternalNumbers
from ebl.transliteration.domain.museum_number import MuseumNumber


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
    atf_string, tmp_path, database, fragment_repository, glossary=""
):
    atf_importer = AtfImporter(database, fragment_repository)
    create_file(tmp_path / "import/test.atf", atf_string)
    create_file(tmp_path / "import/glossary/akkadian.glo", glossary)
    atf_importer.run_importer(
        {
            "input_dir": tmp_path / "import",
            "logdir": tmp_path / "logs",
            "glodir": tmp_path / "import/glossary",
            "author": "Test author",
        }
    )


def check_importing_and_logs(
    museum_number, fragment_repository, tmp_path, logs_check=True
):
    fragment = fragment_repository.query_by_museum_number(
        MuseumNumber.of(museum_number)
    )
    assert str(fragment.number) == museum_number
    if logs_check:
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
    museum_number = "BM.1"
    atf = f"&P111111 = {museum_number}\n1'. GU₄ 30 ⸢12⸣ [...]"
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


def test_fragment_update_cancel_by_user(
    database, fragment_repository, tmp_path, mock_input
):
    museum_number = "BM.333"
    atf = f"&P000001 = {museum_number}\n1. GU₄ 30 ⸢12⸣ [...]"
    fragment_repository.create(
        FragmentFactory.build(number=MuseumNumber.of(museum_number))
    )
    setup_and_run_importer(atf, tmp_path, database, fragment_repository)
    check_importing_and_logs(museum_number, fragment_repository, tmp_path)
    # ToDo: Implement


def test_import_fragment_parsing_errors(
    database, fragment_repository, tmp_path, mock_input
):
    pass
    # ToDo: Implement


def test_import_fragment_correct_parsing_errors(
    database, fragment_repository, tmp_path, mock_input
):
    pass
    # ToDo: Implement


# ToDo: Add tests for:
# - importing multiple files
# - importing files with lemmatization & multiple glossaries
# - ask before updating existing edition
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
        "64. * ina {iti}ZIZ₂ U₄ 14.KAM AN.KU₁₀ 30 GAR-ma <<ina>> KAN₅-su KU₄ DINGIR GU₇\n"
        "#lem: šumma[if]CNJ; ina[in]PRP; Šabāṭu[Month XI]MN; ūmu[day]N; n; antallû[eclipse]N; Sîn["
        "moon]N; šakānu[take place]V; adrūssu[darkly]AV; erēbu[enter]V; ilu["
        "god]N; ikkal[eat]V"
    )
    glossary = (
        "@project test/test_lemmatization\n"
        "@lang    akk\n"
        "@name    akk\n\n"
        "@letter A\n\n"
        "@entry adrūssu [darkly] AV\n"
        "@form KAN₅-su $adrūssu\n"
        "@sense AV darkly\n"
        "@end entry\n\n"
        "@entry akālu [eat] V\n"
        "@form KU₂ $akālu\n"
        "@sense V eat\n"
        "@end entry\n\n"
        "@entry antallû [eclipse] N\n"
        "@form AN.KU₁₀ $antallû\n"
        "@sense N eclipse\n"
        "@end entry\n\n"
        "@letter E\n\n"
        "@entry erēbu [enter] V\n"
        "@form KU₄ $erēbu\n"
        "@sense V enter\n"
        "@sense V fall\n"
        "@end entry\n\n"
        "@letter I\n\n"
        "@entry ilu [god] N\n"
        "@form DINGIR $ilu\n"
        "@form DINGIR{MEŠ} $ilu\n"
        "@sense N god\n"
        "@end entry\n\n"
        "@entry ina [in] PRP\n"
        "@form ina $ina\n"
        "@form in $ina\n"
        "@sense PRP in\n"
        "@sense PRP during\n"
        "@sense PRP at (plus numeral)\n"
        "@end entry\n\n"
        "@letter S\n\n"
        "@entry Sîn [moon(-god)] N\n"
        "@form sin $Sîn\n"
        "@sense N moon\n"
        "@end entry\n\n"
        "@letter Š\n\n"
        "@entry Šabāṭu [Month XI] MN\n"
        "@form ZIZ₂ %akk $Šabāṭu\n"
        "@form {ITU}ZIZ₂ %akk $Šabāṭu\n"
        "@sense MN Month XI\n"
        "@end entry\n\n"
        "@entry šakānu [put] V\n"
        "@form GAR $šakānu\n"
        "@form GAR-ma $šakānu\n"
        "@sense V take place\n"
        "@end entry\n\n"
        "@entry šumma [if] CNJ\n"
        "@form DIŠ $šumma\n"
        "@sense CNJ if\n"
        "@end entry\n\n"
        "@letter U\n\n"
        "@entry ūmu [day] N\n"
        "@form U₄{ME} $ūmu\n"
        "@form UD $ūmu\n"
        "@form ME $ūmu\n"
        "@form U₄ $ūmu\n"
        "@sense N day\n"
        "@sense N first appearance\n"
        "@sense N daytime\n"
        "@end entry"
    )

    setup_and_run_importer(atf, tmp_path, database, fragment_repository, glossary)
    check_importing_and_logs(
        museum_number, fragment_repository, tmp_path, logs_check=False
    )
    fragment = fragment_repository.query_by_museum_number(
        MuseumNumber.of(museum_number)
    )
    assert [word.unique_lemma for word in fragment.text.lines[0]._content] == [
        ("DIŠ", ("šumma I",)),
        ("ina", ("ina I",)),
        ("{iti}ZIZ₂", ("Šabāṭu I",)),
        ("U₄", ("ūmu I",)),
        ("14.KAM", ()),
        ("AN.KU₁₀", ("antalû I",)),
        ("30", ("Sîn I",)),
        ("GAR-ma", ("šakānu I",)),
        ("<<ina>>", ()),
        ("KAN₅-su", ("adru I")), # Fix!
        ("KU₄", ("erēbu I",)),
        ("DINGIR", ("ilu I",)),
        ("GU₇", ("akālu I")), # Fix!
    ]


# @pytest.mark.skip(reason="heavy test")
def test_atf_importer(fragment_repository):
    client = MongoClient(os.environ["MONGODB_URI"])
    database = client.get_database(os.environ.get("MONGODB_DB"))
    atf_importer = AtfImporter(database, fragment_repository)
    archive = zipfile.ZipFile("ebl/tests/atf_importer/test_data.zip")
    with tempfile.TemporaryDirectory() as tempdir:
        data_path = f"{tempdir}/test_atf_import_data"
        archive.extractall(data_path)
        for dir in os.listdir(data_path):
            glossary_path = f"{data_path}/{dir}"
            atf_dir_path = f"{data_path}/{dir}/00atf"
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
