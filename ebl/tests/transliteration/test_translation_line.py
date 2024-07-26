import pytest

from ebl.lemmatization.domain.lemmatization import LemmatizationToken
from ebl.transliteration.domain.atf import Atf, Surface
from ebl.transliteration.domain.labels import ColumnLabel, SurfaceLabel
from ebl.transliteration.domain.line_number import LineNumber
from ebl.transliteration.domain.markup import StringPart
from ebl.transliteration.domain.translation_line import Extent, TranslationLine


@pytest.mark.parametrize(
    "parts,language,extent,prefix,translation",
    [
        ((StringPart("foo"), StringPart("bar")), "en", None, "#tr.en", "foobar"),
        ((StringPart("foo"),), "de", Extent(LineNumber(1)), "#tr.de.(1)", "foo"),
        (
            (StringPart("foo"),),
            "de",
            Extent(
                LineNumber(1),
                (SurfaceLabel((), Surface.OBVERSE), ColumnLabel((), 2)),
            ),
            "#tr.de.(o ii 1)",
            "foo",
        ),
    ],
)
def test_parallel_fragment(parts, language, extent, prefix, translation) -> None:
    line = TranslationLine(parts, language, extent)

    assert line.parts == parts
    assert line.language == language
    assert line.extent == extent
    assert line.translation == translation
    assert line.atf == Atf(f"{prefix}: {translation}")
    assert line.lemmatization == (LemmatizationToken(translation),)
