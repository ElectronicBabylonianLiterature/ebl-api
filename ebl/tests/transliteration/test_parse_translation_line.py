import pytest

from ebl.transliteration.domain.lark_parser import parse_atf_lark
from ebl.transliteration.domain.markup import StringPart
from ebl.transliteration.domain.text import Text
from ebl.transliteration.domain.translation_line import Extent, TranslationLine
from ebl.transliteration.domain.labels import ColumnLabel, SurfaceLabel
from ebl.transliteration.domain.line_number import LineNumber
from ebl.transliteration.domain.atf import Surface


@pytest.mark.parametrize(
    "atf,expected_line",
    [
        (
            "#tr.en: translation",
            TranslationLine((StringPart("translation"),), "en", None),
        ),
        (
            "#tr.ar.(2): translation",
            TranslationLine(
                (StringPart("translation"),), "ar", Extent(LineNumber(2), tuple())
            ),
        ),
        (
            "#tr.de.(o iii 1): translation",
            TranslationLine(
                (StringPart("translation"),),
                "de",
                Extent(
                    LineNumber(1),
                    (SurfaceLabel(tuple(), Surface.OBVERSE), ColumnLabel(tuple(), 3)),
                ),
            ),
        ),
    ],
)
def test_parse_translation_line(atf, expected_line) -> None:
    assert parse_atf_lark(atf).lines == Text.of_iterable([expected_line]).lines
