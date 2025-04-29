import os
import zipfile
import tempfile
import builtins
import pytest
from ebl.atf_importer.application.atf_importer import AtfImporter
from ebl.atf_importer.domain.legacy_atf_converter import LegacyAtfConverter
from ebl.atf_importer.application.lines_getter import EblLinesGetter
from ebl.tests.factories.fragment import FragmentFactory
from ebl.fragmentarium.domain.fragment_external_numbers import ExternalNumbers


def create_file(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.touch()
    path.write_text(content)


def setup_and_run(atf_content, tmp_path, database):
    atf_importer = AtfImporter(database)
    create_file(tmp_path / "import/test.atf", atf_content)
    create_file(tmp_path / "import/akkadian.glo", "")
    atf_importer.run_importer(
        {
            "input_dir": tmp_path / "import",
            "logdir": tmp_path / "logs",
            "glossary_path": tmp_path / "import/akkadian.glo",
            "author": "Test author",
        }
    )


@pytest.fixture
def mock_input(monkeypatch):
    def _set_input_responses(responses):
        responses_iter = iter(responses)
        monkeypatch.setattr(builtins, "input", lambda *args: next(responses_iter))
        return responses_iter

    return _set_input_responses


def test_logger_writes_files(database, fragment_repository, tmp_path):
    setup_and_run("&P000001 = BM.1\n1'. GU₄ 30 ⸢12⸣ [...]", tmp_path, database)
    assert os.listdir(tmp_path / "logs") == [
        "imported_files.txt",
        "not_imported_files.txt",
        "error_lines.txt",
        "not_lemmatized_tokens.txt",
        "unparsable_lines.txt",
    ]
    for log_file in os.listdir(tmp_path / "logs"):
        with open(tmp_path / f"logs/{log_file}") as logfile:
            if log_file == "not_imported_files.txt":
                # ToDo: Update assertion. The file should be listed in imported_files.txt
                assert logfile.read() == ""


def test_find_museum_number_by_cdli_number(database, fragment_repository, tmp_path):
    fragment_repository.create(
        FragmentFactory.build(
            number="BM.111", external_numbers=ExternalNumbers(cdli_number="P111111")
        )
    )
    setup_and_run("&P111111 = BM.111\n1'. GU₄ 30 ⸢12⸣ [...]", tmp_path, database)
    # ToDo: Add assertion to check that the data was imported


def test_find_museum_number_by_traditional_reference(
    database, fragment_repository, tmp_path
):
    fragment_repository.create(
        FragmentFactory.build(
            number="BM.111", traditional_references=["test reference"]
        )
    )
    setup_and_run("&P000001 = test reference\n. GU₄ 30 ⸢12⸣ [...]", tmp_path, database)
    # ToDo: Add assertion to check that the data was imported


def test_no_museum_number_in_database_input(
    database, fragment_repository, tmp_path, mock_input
):
    responses = mock_input(["BM.2", "end"])
    setup_and_run("&P000001 = test reference\n. GU₄ 30 ⸢12⸣ [...]", tmp_path, database)
    assert next(responses) == "end"
    # ToDo: Add assertion to check that the data was imported


def test_no_museum_number_in_database_skip(
    database, fragment_repository, tmp_path, mock_input
):
    responses = mock_input(["skip", "end"])
    setup_and_run("&P000001 = test reference\n. GU₄ 30 ⸢12⸣ [...]", tmp_path, database)
    assert next(responses) == "end"
    # ToDo: Add assertion to check that the data was not imported


def test_import_existing_fragment():
    pass
    # ToDo: Implement


def test_import_existing_fragment_reject():
    pass
    # ToDo: Implement


def test_import_fragment_parsing_errors():
    pass
    # ToDo: Implement


def test_import_fragment_correct_parsing_errors():
    pass
    # ToDo: Implement


def test_placeholder_insert(database):
    """
    Test case for insertion of placeholder if '<<'.
    """
    legacy_atf_converter = LegacyAtfConverter()
    converted_lines = legacy_atf_converter.convert_lines_from_string(
        "64. * ina {iti}ZIZ₂ U₄ 14.KAM AN.GE₆ 30 GAR-ma <<ina>> KAN₅-su KU₄ DINGIR GU₇\n"
        "#lem: ina[in]PRP; Šabaṭu[1]MN; ūmu[day]N; n; attalli[eclipse]N; Sin["
        "1]DN; iššakkanma[take place]V; adrūssu[darkly]AV; īrub[enter]V; ilu["
        "god]N; ikkal[eat]V"
    )

    test_lemmas = [
        [],
        ["Šabaṭu I"],
        [],
        [],
        [],
        ["Sin I"],
        [],
        [],
        [],
        [],
        [],
    ]
    atf_importer = AtfImporter(database)
    atf_importer._ebl_lines_getter = EblLinesGetter(
        atf_importer.database,
        atf_importer.config,
        atf_importer.logger,
        {},  # ToDo: Add GlossaryParserData?
        test_lemmas,  # ToDo: Better implement mocking
    )
    ebl_lines = atf_importer.convert_to_ebl_lines(
        converted_lines,
        "cpp_3_1_16",
    )

    # ToDo: Fix error:
    # FAILED ebl/tests/atf_importer/test_atf_importer.py:
    #   :test_placeholder_insert - KeyError: 'last_transliteration'
    print("!!!! ebl_lines", ebl_lines)
    assert len(ebl_lines["last_transliteration"]) == len(ebl_lines["all_unique_lemmas"])


def test_atf_importer(database):
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
                    "glossary_path": glossary_akk_path,
                    "author": "Test author",
                }
            )

            """
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
            """

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
