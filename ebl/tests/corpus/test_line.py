import pytest

from ebl.transliteration.domain.translation_line import Extent, TranslationLine
from ebl.transliteration.domain.atf import Surface
from ebl.transliteration.domain.line_number import LineNumber
from ebl.transliteration.domain.labels import SurfaceLabel
from ebl.corpus.domain.line import Line


def test_invalid_extent() -> None:
    translation = TranslationLine(
        tuple(), extent=Extent(LineNumber(1), (SurfaceLabel(tuple(), Surface.OBVERSE),))
    )

    with pytest.raises(
        ValueError, match="Labels are not allowed in line translations."
    ):
        Line(LineNumber(1), tuple(), translation=(translation,)),
