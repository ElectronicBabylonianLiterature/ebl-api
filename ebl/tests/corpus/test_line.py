import pytest

from ebl.corpus.domain.line import Line
from ebl.transliteration.domain.atf import Surface
from ebl.transliteration.domain.labels import SurfaceLabel
from ebl.transliteration.domain.line_number import LineNumber
from ebl.transliteration.domain.translation_line import Extent, TranslationLine


def test_invalid_extent() -> None:
    translation = TranslationLine(
        tuple(), extent=Extent(LineNumber(1), (SurfaceLabel(tuple(), Surface.OBVERSE),))
    )

    with pytest.raises(  # pyre-ignore[16]
        ValueError, match="Labels are not allowed in line translations."
    ):
        (Line(LineNumber(1), (), translation=(translation,)),)
