import pytest
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
@(2) @i{my}@sup{?} @sup{father}
@(3) @Bēlšunu"""

TRANSLATION_EXPECTED_D = """1. a-na
#tr.en: @sub{To}
2. a-bi₂-ya
#tr.en: @i{my}@sup{?} @sup{father}
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

TRANSLATION_LEGACY_F = """@obverse
@column
1. a-na
2. a-bí-ya
@reverse
1. {m}EN-šu-nu
@translation labeled en project
@(o i 1) To
@(o i 2) my father
@(r 1) Bēlšunu"""

TRANSLATION_EXPECTED_F = """@obverse
@column 1
1. a-na
#tr.en: To
2. a-bi₂-ya
#tr.en: my father
@reverse
1. {m}EN-šu-nu
#tr.en: Bēlšunu"""

TRANSLATION_LEGACY_G = """@obverse
@column
A1'. a-na
A2'. a-bí-ya
@reverse
B1. {m}EN-šu-nu
@translation labeled en project
@(o i A1') To
@(o i A2') my father
@(r B1) Bēlšunu"""

TRANSLATION_EXPECTED_G = """@obverse
@column 1
A1'. a-na
#tr.en: To
A2'. a-bi₂-ya
#tr.en: my father
@reverse
B1. {m}EN-šu-nu
#tr.en: Bēlšunu"""


@pytest.mark.parametrize(
    "legacy_atf,expected_atf",
    [
        (
            TRANSLATION_LEGACY_A,
            TRANSLATION_EXPECTED_A,
        ),
        (
            TRANSLATION_LEGACY_B,
            TRANSLATION_EXPECTED_B,
        ),
        (
            TRANSLATION_LEGACY_C,
            TRANSLATION_EXPECTED_C,
        ),
        (
            TRANSLATION_LEGACY_D,
            TRANSLATION_EXPECTED_D,
        ),
        (
            TRANSLATION_LEGACY_E,
            TRANSLATION_EXPECTED_E,
        ),
        (
            TRANSLATION_LEGACY_F,
            TRANSLATION_EXPECTED_F,
        ),
        (
            TRANSLATION_LEGACY_G,
            TRANSLATION_EXPECTED_G,
        ),
    ],
)
def test_legacy_translation(database, legacy_atf, expected_atf):
    legacy_atf_converter = LegacyAtfConverter(database, config, logger)
    expected_lines = parse_atf_lark(expected_atf)
    legacy_lines = legacy_atf_converter.convert_lines_from_string(
        legacy_atf.strip("\n")
    )[1]
    assert legacy_lines == expected_lines
