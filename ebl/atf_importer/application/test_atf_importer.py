from ebl.atf_importer.domain.atf_preprocessor import ATFPreprocessor
from ebl.atf_importer.domain.atf_preprocessor_util import Util
from ebl.atf_importer.application.atf_importer import ATFImporter
import unittest


class Test_ATF_Importer(unittest.TestCase):

    # Test case for insertion of placeholder if "<<"
    def test_placeholder_insert(self):
        atf_preprocessor = ATFPreprocessor("../logs")
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

        # import test lines
        a = ATFImporter()
        a.lemmas_cfforms = Util.get_test_lemmas_cfforms()
        a.cfforms_senes = Util.get_test_cfforms_senses()
        a.cfform_guideword = Util.get_test_cfform_guidword()
        ebl_lines = a.convert_to_ebl_lines(converted_lines, "cpp_3_1_16")

        self.assertEqual(
            len(ebl_lines["last_transliteration"]), len(ebl_lines["all_unique_lemmas"])
        )
