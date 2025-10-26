import pytest
import json
from ebl.atf_importer.domain.legacy_atf_converter import LegacyAtfConverter
from ebl.atf_importer.application.logger import Logger
from ebl.transliteration.domain.atf_parsers.lark_parser import parse_atf_lark
from ebl.atf_importer.application.atf_importer_config import (
    AtfImporterConfig,
)


logger = Logger("../logs")
config = AtfImporterConfig().config_data


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
1. a-na?
2. a-bí-ya
3. {m}EN-šu-nu
@translation labeled en project
@(r.e.? i 1) @?To?@
@(r.e.? i 2) my @"father"@
@(r.e.? i 3) @Bēlšunu"""

TRANSLATION_EXPECTED_B = """@right?
@column 1
1. a-na?
#tr.en: @i{To}
2. a-bi₂-ya
#tr.en: my “father”
3. {m}EN-šu-nu
#tr.en: @i{Bēlšunu}"""

TRANSLATION_LEGACY_C = """1'. a-na?
2'. a-bí-ya
3'. {m}EN-šu-nu
@translation labeled en project
@(1') To
@(2') my father
@(3') Bēlšunu"""

TRANSLATION_EXPECTED_C = """1'. a-na?
#tr.en: To
2'. a-bi₂-ya
#tr.en: my father
3'. {m}EN-šu-nu
#tr.en: Bēlšunu"""

TRANSLATION_LEGACY_D = """1. a-na
2. a-bí-ya
3. {m}EN-šu-nu
@translation labeled en project
@(1) @sub{To}
@(2) my @sup{father}
@(3) @Bēlšunu"""

TRANSLATION_EXPECTED_D = """1. a-na
#tr.en: @sub{To}
2. a-bi₂-ya
#tr.en: my @sup{father}
3. {m}EN-šu-nu
#tr.en: @i{Bēlšunu}"""

TRANSLATION_LEGACY_E = """@obverse
@column
$ ruling
1. a-na
2. a-bí-ya
3. {m}EN-šu-nu
$ rest broken
@translation labeled en project
@obverse
$ ruling
@(o i 1) To
@(o i 2) my father
@(o i 3) Bēlšunu
$ rest broken"""

TRANSLATION_EXPECTED_E = """@obverse
@column 1
$ single ruling
1. a-na
#tr.en: To
2. a-bi₂-ya
#tr.en: my father
3. {m}EN-šu-nu
#tr.en: Bēlšunu
$ rest of side broken"""


PARSE_AND_TRANSFORM_LEGACY = [
    ("", ""),
    ("@column", "@column 1"),
    ("@column\n@column", "@column 1\n@column 2"),
    ("@face a", "@face a"),
    ("@obverse", "@obverse"),
    ("@reverse", "@reverse"),
    ("$ obverse broken", "$ obverse broken"),
    ("$ rest broken", "$ rest of side broken"),
    ("$ ((rest of column broken))", "$ rest of column broken"),
    ("$ (((rest of column broken)))", "$ rest of column broken"),
    ("$ ruling", "$ single ruling"),
    ("$ ruling?", "$ single ruling?"),
    ("$ seal impression", "$ (seal impression)"),
    ("$ seal impression broken", "$ (seal impression broken)"),
    ("# note: some note", "#note: some note"),
    ("# some note", "#note: some note"),
    ("1. kur    \t  \t kur", "1. kur kur"),
    ("1. kur\tkur\r", "1. kur kur"),
    ("1. x[x]x ⸢x⸣[x]⸢x⸣ ⌈x⌉[x]⌈x⌉", "1. x [x] x x# [x] x# x# [x] x#"),
    ("1. [kur]? [kur]! [kur]?! [kur]!?", "1. [kur?] [kur!] [kur?!] [kur!?]"),
    ("1. [kur]₃ [x x a]₃ a[₃ x x]", "1. [ku]r₃ [x x] a₃# a₃# [x x]"),
    ("1. ⸢kur⸣? ⌈kur⌉! ⸢kur⸣?! ⌈kur⌉!?", "1. kur?# kur!# kur?!# kur!?#"),
    ("1. ($$) kur ($anything12 345!@$)", "1. ($___$) kur ($___$)"),
    ("1. a–a a--a", "1. a-a a-a"),
    ("1. sza ca s,a t,a ḫa ja ŋa g̃a 'a", "1. ša ša ṣa ṭa ha ga ga ga ʾa"),
    ("1. SZA CA S,A T,A ḪA JA ŊA G̃A", "1. ŠA ŠA ṢA ṬA HA GA GA GA"),
    ("1. {f}DUB.SAR", "1. {munus}DUB.SAR"),
    ("1. 1/2 1/3 1/4 1/5 1/6 2/3 5/6", "1. ½ ⅓ ¼ ⅕ ⅙ ⅔ ⅚"),
    ("1. _a-a_", "1. A.A"),
    ("1. {GISZ}GIGIR", "1. {giš}GIGIR"),
    ("1′. A", "1'. A"),
    ("1’. A", "1'. A"),
    ("1ʾ. A", "1'. A"),
    ("1. 4(BÁN)? 4(BÁN)! 4(BÁN)?!", "1. 4?(BAN₂) 4!(BAN₂) 4?!(BAN₂)"),
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
        "1. [*] ⸢AN⸣.GE₆ GAR-ma U₄ ŠÚ{+up} * AN.GE₆ GAR-ma {d}IŠKUR KA-šú ŠUB{"
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
        "57. {MULₓ(ÁB)}GU.LA KI* ŠÈG ⸢KI*⸣ {kur}NIM.MA{ki} iš-kar* ÀM.GAL É.GAL : "
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
def test_text_lines(database, legacy_lines, ebl_lines):
    legacy_atf_converter = LegacyAtfConverter(database, config, logger)
    legacy_lines = legacy_atf_converter.convert_lines_from_string(legacy_lines)[1]
    expected_lines = parse_atf_lark(ebl_lines)
    assert legacy_lines == expected_lines


def test_legacy_translation(database):
    legacy_atf_converter = LegacyAtfConverter(database, config, logger)
    translations = [
        TRANSLATION_LEGACY_A,
        TRANSLATION_LEGACY_B,
        TRANSLATION_LEGACY_C,
        TRANSLATION_LEGACY_D,
        TRANSLATION_LEGACY_E,
    ]
    expected = [
        TRANSLATION_EXPECTED_A,
        TRANSLATION_EXPECTED_B,
        TRANSLATION_EXPECTED_C,
        TRANSLATION_EXPECTED_D,
        TRANSLATION_EXPECTED_E,
    ]
    for index, TRANSLATION_LEGACY in enumerate(translations):
        expected_lines = parse_atf_lark(expected[index])
        legacy_lines = legacy_atf_converter.convert_lines_from_string(
            TRANSLATION_LEGACY.strip("\n")
        )[1]
        assert legacy_lines == expected_lines


lemma_lines = []
with open("ebl/tests/atf_importer/test_lemma_lines.json", "r") as file:
    lemma_lines: list = json.load(file)


@pytest.mark.parametrize("line", lemma_lines)
def test_lemma_line_c_type_is_lem_line(database, line):
    legacy_atf_converter = LegacyAtfConverter(database, config, logger)
    result = legacy_atf_converter.convert_lines([line])[0]

    assert result["c_type"] == "lem_line"
