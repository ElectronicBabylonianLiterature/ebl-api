import pytest
import json
from ebl.atf_importer.domain.atf_preprocessor import AtfPreprocessor

PROBLEMATIC_TEXT_LINES = [
    (
        "1. ŠÚ ù ŠÚ<(šumma)> |ŠÚ+ŠÚ|",
        "1. ŠU₂ u₃ ŠU₂<(šumma)> |ŠU₂+ŠU₂|",
    ),
    (
        "1. [*] * *-*",
        "1. [DIŠ] DIŠ DIŠ-DIŠ",
    ),
    (
        "1. ŠU2 u3 ŠU2<(šumma)> |ŠU2+ŠU2|",
        "1. ŠU₂ u₃ ŠU₂<(šumma)> |ŠU₂+ŠU₂|",
    ),
    (
        "1. [*] AN#.GE₆ GAR-ma U₄ ŠÚ{+up} * AN.GE₆ GAR-ma {d}IŠKUR KA-šú ŠUB{"
        "+di} * AN.GE₆",
        "1. [DIŠ] AN#.GE₆ GAR-ma U₄ ŠU₂{+up} DIŠ AN.GE₆ GAR-ma {d}IŠKUR KA-šu₂ "
        "ŠUB{+di} DIŠ AN.GE₆",
    ),
    (
        "8. KAR <:> e-ṭe-ri :* KAR : e-ke-mu : LUGAL ina di-bi-ri : LUGAL ina "
        "ud-da-a-ta",
        "8. KAR < : > e-ṭe-ri :* KAR : e-ke-mu : LUGAL ina di-bi-ri : LUGAL ina "
        "ud-da-a-ta",
    ),
    (
        "14. [...] x (x) še-e-hu $BAD $É $ME : ina GAŠAN-ia₅ {d}SUEN {"
        "d}INANA--<É>.AN.NA",
        "14. [...] x (x) še-e-hu BAD E₂ ME : ina GAŠAN-ia₅ {d}SUEN {"
        "d}INANA-<E₂>.AN.NA",
    ),
]


FOLLOWING_SIGN_IS_NOT_A_LOGOGRAM = (
    "5'.	[...] x [...] x-šu₂? : kal : nap-ha-ri : $WA-wa-ru : ia-ar₂-ru",
    "5'. [...] x [...] x-šu₂? : kal : nap-ha-ri : WA-wa-ru : ia-ar₂-ru",
)

LEGACY_GRAMMAR_SIGNS = [
    (
        "57. {mulₓ(ÁB)}GU.LA KI* ŠÈG KI*# {kur}NIM.MA{ki} iš-kar* ÀM.GAL É.GAL : "
        "ANŠE.KUR.RA-MEŠ",
        "57. {mulₓ(AB₂)}GU.LA KI* ŠEG₃ KI*# {kur}NIM.MA{ki} iš-kar* AM₃.GAL E₂.GAL : "
        "ANŠE.KUR.RA-MEŠ",
    ),
]


@pytest.mark.parametrize(
    "legacy_line,ebl_line",
    [*PROBLEMATIC_TEXT_LINES, FOLLOWING_SIGN_IS_NOT_A_LOGOGRAM, *LEGACY_GRAMMAR_SIGNS],
)
def test_text_lines(legacy_line, ebl_line):
    # ToDo: fix
    atf_preprocessor = AtfPreprocessor("../logs", 0)
    legacy_tree = atf_preprocessor.ebl_parser.parse(legacy_line)
    legacy_tree = atf_preprocessor.transform_legacy_atf(legacy_tree)

    expected_tree = atf_preprocessor.ebl_parser.parse(ebl_line)
    # (converted_line,) = atf_preprocessor.process_line(legacy_line)
    print('RESULT:\n', legacy_tree.pretty())
    print('EXPECTED:\n', expected_tree.pretty())

    assert legacy_tree == expected_tree


lemma_lines = []
with open("ebl/tests/atf_importer/test_lemma_lines.json", "r") as file:
    lemma_lines: list = json.load(file)


@pytest.mark.parametrize("line", lemma_lines)
def test_lemma_line_c_type_is_lem_line(line):
    atf_preprocessor = AtfPreprocessor("../logs", 0)

    (
        converted_line,
        c_array,
        c_type,
        c_alter_lem_line_at,
    ) = atf_preprocessor.process_line(line)

    assert c_type == "lem_line"
