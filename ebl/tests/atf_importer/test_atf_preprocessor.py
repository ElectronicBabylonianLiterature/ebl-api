import pytest
import json
from ebl.atf_importer.domain.atf_preprocessor import AtfPreprocessor
from ebl.transliteration.domain.atf_parsers.lark_parser import parse_translation_line

TRANSLATION_LEGACY_A = """@right?
@column
1. a-na
2. a-bí-ya
@translation en labelled
@label(r.e.? i 1-r.e.? i 2)
To my
father"""

TRANSLATION_EXPECTED_A = """@right?
@column 1
1. a-na
#tr.en.(r.e.? i 2): To my father
2. a-bi₂-ya"""

TRANSLATION_LEGACY_B = """@right?
@column
1. a-na
2. a-bí-ya
@translation labeled en project
@(r.e.? i 1) To my
@(r.e.? i 2) father"""

TRANSLATION_EXPECTED_B = """@right?
@column 1
1. a-na
#tr.en: To my
2. a-bi₂-ya
#tr.en: father"""

PARSE_AND_TRANSFORM_LEGACY = [
    ("", ""),
    ("@column", "@column 1"),
    ("@column\n@column", "@column 1\n@column 2"),
    ("@face a", "@face a"),
    ("@obverse", "@obverse"),
    ("@reverse", "@reverse"),
    ("$ obverse broken", "$ obverse broken"),
    ("$ rest broken", "$ rest of side broken"),
    ("$ ruling", "$ single ruling"),
    ("$ ruling?", "$ single ruling?"),
    ("1. a'", "1. aʾ"),
    ("1′. A", "1'. A"),
    ("1’. A", "1'. A"),
    (
        "1. ⸢4?(BÁN)⸣",
        "1. 4?#(BAN₂#)",
    ),
    ("1. LU2~v", "1. LU₂@v"),
    ("1. u2~v", "1. u₂@v"),
    ("1. 2~v", "1. 2@v"),
    ("1. $BAD.$É $ME", "1. BAD.E₂ ME"),
    ("1. ⸢16?! 15! 12⸣ 17", "1. 16?!# 15!# 12# 17"),
    ("1. $BAD.$É $ME", "1. BAD.E₂ ME"),
    (
        "1. {d}INANA--<É>.AN.NA",
        "1. {d}INANA-<E₂>.AN.NA",
    ),
    (
        "1. ŠÚ ù ŠÚ<(šumma)> |ŠÚ+ŠÚ|",
        "1. ŠU₂ u₃ ŠU₂<(šumma)> |ŠU₂+ŠU₂|",
    ),
    (
        "1. ŠU2 u3 ŠU2<(šumma)> |ŠU2+ŠU2|",
        "1. ŠU₂ u₃ ŠU₂<(šumma)> |ŠU₂+ŠU₂|",
    ),
    (
        "1. [*] * *-*",
        "1. [DIŠ] DIŠ DIŠ-DIŠ",
    ),
    (
        "1. <:>",
        "1. < : >",
    ),
]

PROBLEMATIC_TEXT_LINES = [
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
        "14. [...] x (x) še-e-hu BAD E₂ ME : ina GAŠAN-ia₅ {d}SUEN {d}INANA-<E₂>.AN.NA",
    ),
]


FOLLOWING_SIGN_IS_NOT_A_LOGOGRAM = [
    (
        "5'. [...] x [...] x-šu₂? : kal : nap-ha-ri : $WA-wa-ru : ia-ar₂-ru",
        "5'. [...] x [...] x-šu₂? : kal : nap-ha-ri : WA-wa-ru : ia-ar₂-ru",
    )
]

LEGACY_GRAMMAR_SIGNS = [
    (
        "57. {mulₓ(ÁB)}GU.LA KI* ŠÈG KI*# {kur}NIM.MA{ki} iš-kar* ÀM.GAL É.GAL : "
        "ANŠE.KUR.RA-MEŠ",
        "57. {mulₓ(AB₂)}GU.LA KI* ŠEG₃ KI*# {kur}NIM.MA{ki} iš-kar* AM₃.GAL E₂.GAL : "
        "ANŠE.KUR.RA-MEŠ",
    ),
]


@pytest.mark.parametrize(
    "legacy_lines,ebl_lines",
    [
        *PARSE_AND_TRANSFORM_LEGACY,
        *PROBLEMATIC_TEXT_LINES,
        *FOLLOWING_SIGN_IS_NOT_A_LOGOGRAM,
        *LEGACY_GRAMMAR_SIGNS,
    ],
)
def test_text_lines(legacy_lines, ebl_lines):
    atf_preprocessor = AtfPreprocessor("../logs", 0)
    legacy_lines = atf_preprocessor.convert_lines_from_string(legacy_lines)
    expected_lines = [
        atf_preprocessor.line_transformer.transform(
            atf_preprocessor.ebl_parser.parse(line)
        )
        for line in ebl_lines.split("\n")
    ]

    assert legacy_lines == expected_lines


def test_legacy_translation():
    atf_preprocessor = AtfPreprocessor("../logs", 0)
    translations = [
        TRANSLATION_LEGACY_A,
        TRANSLATION_LEGACY_B,
    ]
    expected = [
        TRANSLATION_EXPECTED_A,
        TRANSLATION_EXPECTED_B,
    ]
    for index, TRANSLATION_LEGACY in enumerate(translations):
        expected_lines = [
            parse_translation_line(line)
            if "#tr" in line
            else atf_preprocessor.line_transformer.transform(
                atf_preprocessor.ebl_parser.parse(line)
            )
            for line in expected[index].split("\n")
        ]
        legacy_lines = atf_preprocessor.convert_lines_from_string(
            TRANSLATION_LEGACY.strip("\n")
        )
        assert legacy_lines == expected_lines


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
