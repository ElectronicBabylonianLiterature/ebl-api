import os
import zipfile
import tempfile
from ebl.atf_importer.application.atf_importer import AtfImporter
from ebl.atf_importer.domain.legacy_atf_converter import LegacyAtfConverter
from ebl.atf_importer.application.lines_getter import EblLinesGetter
from ebl.atf_importer.application.logger import Logger

logger = Logger("../logs")


def test_placeholder_insert(database):
    """
    Test case for insertion of placeholder if '<<'.
    """
    legacy_atf_converter = LegacyAtfConverter(logger)
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
