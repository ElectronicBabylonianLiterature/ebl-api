from ebl.atf_importer.application.atf_importer import AtfImporter
from ebl.atf_importer.domain.atf_preprocessor import AtfPreprocessor
from ebl.atf_importer.application.lines_getter import EblLinesGetter


def test_placeholder_insert(database):
    """
    Test case for insertion of placeholder if '<<'.
    """
    atf_preprocessor = AtfPreprocessor("../logs", 0)
    converted_lines = []
    c_line, c_array, c_type, c_alter_lemline_at = atf_preprocessor.process_line(
        "64. * ina {iti}ZIZ₂ U₄ 14.KAM AN.GE₆ 30 GAR-ma <<ina>> KAN₅-su KU₄ "
        "DINGIR GU₇"
    )
    converted_lines.append(
        {
            "c_line": c_line,
            "c_array": c_array,
            "c_type": c_type,
            "c_alter_lemline_at": c_alter_lemline_at,
        }
    )
    c_line, c_array, c_type, c_alter_lemline_at = atf_preprocessor.process_line(
        "#lem: ina[in]PRP; Šabaṭu[1]MN; ūmu[day]N; n; attalli[eclipse]N; Sin["
        "1]DN; iššakkanma[take place]V; adrūssu[darkly]AV; īrub[enter]V; ilu["
        "god]N; ikkal[eat]V"
    )
    converted_lines.append(
        {
            "c_line": c_line,
            "c_array": c_array,
            "c_type": c_type,
            "c_alter_lemline_at": c_alter_lemline_at,
        }
    )
    atf_importer = AtfImporter(database)
    atf_importer._ebl_lines_getter = EblLinesGetter(
        atf_importer.database,
        atf_importer.config,
        atf_importer.logger,
        {},  # ToDo: Add glossaryData
    )
    ebl_lines = atf_importer.convert_to_ebl_lines(
        converted_lines,
        "cpp_3_1_16",
        # ToDo: Check if the implementation is proper
        #
        # True,
        # [[], ["Šabaṭu I"], [], [], [], ["Sin I"], [], [], [], [], []]
    )
    # print(ebl_lines)
    # {'transliteration': ['64. DIŠ ina {iti}ZIZ₂ U₄ 14.KAM
    #   AN.GE₆ 30 GAR-ma <<ina>> KAN₅-su KU₄ DINGIR GU₇']}

    # ToDo: Fix error:
    # FAILED ebl/tests/atf_importer/test_atf_importer.py:
    #   :test_placeholder_insert - KeyError: 'last_transliteration'
    assert len(ebl_lines["last_transliteration"]) == len(ebl_lines["all_unique_lemmas"])
