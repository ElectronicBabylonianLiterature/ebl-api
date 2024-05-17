import pytest
import json
from ebl.atf_importer.domain.atf_preprocessor import AtfPreprocessor


PROBLEMATIC_TEXT_LINES = [
    (
        "1. [*] AN#.GE₆ GAR-ma U₄ ŠU₂{+up} * AN.GE₆ GAR-ma {d}IŠKUR KA-šu₂ ŠUB{"
        "+di} * AN.GE₆",
        "1. [ DIŠ] AN#.GE₆ GAR-ma U₄ ŠU₂{+up} DIŠ AN.GE₆ GAR-ma {d}IŠKUR KA-šu₂ "
        "ŠUB{+di} DIŠ AN.GE₆",
    ),
    (
        "8. KAR <:> e-ṭe-ri :* KAR : e-ke-mu : LUGAL ina di-bi-ri : LUGAL ina "
        "ud-da-a-ta",
        "8. KAR < : > e-ṭe-ri :* KAR : e-ke-mu : LUGAL ina di-bi-ri : LUGAL ina "
        "ud-da-a-ta",
    ),
    (
        "14. [...] x (x) še-e-hu $BAD $E₂ $ME : ina GAŠAN-ia₅ {d}SUEN {"
        "d}INANA--<E₂>.AN.NA",
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
        "57. {mulₓ(AB₂)}GU.LA KI* ŠEG₃ KI*# {kur}NIM.MA{ki} iš-kar* É.GAL : "
        "ANŠE.KUR.RA-MEŠ",
        "57. {mulₓ(AB₂)}GU.LA KI* ŠEG₃ KI*# {kur}NIM.MA{ki} iš-kar* E₂.GAL : "
        "ANŠE.KUR.RA-MEŠ",
    ),
    (
        "57. {mulₓ(AB₂)}GU.LA KI* ŠEG₃ KI*# {kur}NIM.MA{ki} iš-kar* ÁM.GAL : "
        "ANŠE.KUR.RA-MEŠ",
        "57. {mulₓ(AB₂)}GU.LA KI* ŠEG₃ KI*# {kur}NIM.MA{ki} iš-kar* AM₃.GAL : "
        "ANŠE.KUR.RA-MEŠ",
    ),
]


@pytest.mark.parametrize(
    "line,expected",
    [*PROBLEMATIC_TEXT_LINES, FOLLOWING_SIGN_IS_NOT_A_LOGOGRAM, *LEGACY_GRAMMAR_SIGNS],
)
def test_text_lines(line, expected):
    atf_preprocessor = AtfPreprocessor("../logs", 0)

    (
        converted_line,
        c_array,
        c_type,
        c_alter_lemline_at,
    ) = atf_preprocessor.process_line(line)
    assert converted_line == expected


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
        c_alter_lemline_at,
    ) = atf_preprocessor.process_line(line)

    assert c_type == "lem_line"
