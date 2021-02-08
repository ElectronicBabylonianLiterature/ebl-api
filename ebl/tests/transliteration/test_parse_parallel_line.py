import pytest  # pyre-ignore

from ebl.corpus.domain.chapter import Stage
from ebl.corpus.domain.text_id import TextId
from ebl.fragmentarium.domain.museum_number import MuseumNumber
from ebl.transliteration.domain import atf
from ebl.transliteration.domain.labels import SurfaceLabel
from ebl.transliteration.domain.lark_parser import parse_line
from ebl.transliteration.domain.line_number import LineNumber
from ebl.transliteration.domain.parallel_line import (
    ChapterName,
    Genre,
    ParallelComposition,
    ParallelFragment,
    ParallelText,
)


@pytest.mark.parametrize(
    "line,expected_line",
    [
        (
            "// cf. F K.1 &d o! 1",
            ParallelFragment(
                True,
                MuseumNumber.of("K.1"),
                True,
                SurfaceLabel.from_label(atf.Surface.OBVERSE, [atf.Status.CORRECTION]),
                LineNumber(1),
            ),
        ),
        (
            "// F K.1 1",
            ParallelFragment(False, MuseumNumber.of("K.1"), False, None, LineNumber(1)),
        ),
        (
            '// cf. L I.1 OB "my name" 1',
            ParallelText(
                True,
                Genre.LITERATURE,
                TextId(1, 1),
                ChapterName(Stage.OLD_BABYLONIAN, "", "my name"),
                LineNumber(1),
            ),
        ),
        (
            '// cf. L I.1 OB "my version" "my name" 1',
            ParallelText(
                True,
                Genre.LITERATURE,
                TextId(1, 1),
                ChapterName(Stage.OLD_BABYLONIAN, "my version", "my name"),
                LineNumber(1),
            ),
        ),
        (
            "// L I.1 1",
            ParallelText(False, Genre.LITERATURE, TextId(1, 1), None, LineNumber(1)),
        ),
        (
            "// L III.10 1",
            ParallelText(False, Genre.LITERATURE, TextId(3, 10), None, LineNumber(1)),
        ),
        (
            "// L 0.0 1",
            ParallelText(False, Genre.LITERATURE, TextId(0, 0), None, LineNumber(1)),
        ),
        ("// cf. (name 1)", ParallelComposition(True, "name", LineNumber(1))),
        ("// (name 1)", ParallelComposition(False, "name", LineNumber(1))),
    ],
)
def test_parse_atf_at_line(line, expected_line):
    assert parse_line(line) == expected_line
