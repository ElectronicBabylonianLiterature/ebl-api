import pytest

from ebl.corpus.domain.chapter import Stage
from ebl.transliteration.domain.text_id import TextId
from ebl.transliteration.domain.museum_number import MuseumNumber
from ebl.transliteration.domain import atf
from ebl.transliteration.domain.genre import Genre
from ebl.transliteration.domain.labels import ColumnLabel, ObjectLabel, SurfaceLabel
from ebl.transliteration.domain.atf_parsers.lark_parser import parse_line
from ebl.transliteration.domain.line_number import LineNumber
from ebl.transliteration.domain.parallel_line import (
    ChapterName,
    Labels,
    ParallelComposition,
    ParallelFragment,
    ParallelText,
)


@pytest.mark.parametrize(
    "line,expected_line",
    [
        (
            "// cf. F K.1 &d tablet* o! iii? 1",
            ParallelFragment(
                True,
                MuseumNumber.of("K.1"),
                True,
                Labels(
                    ObjectLabel.from_object(atf.Object.TABLET, [atf.Status.COLLATION]),
                    SurfaceLabel.from_label(
                        atf.Surface.OBVERSE, [atf.Status.CORRECTION]
                    ),
                    ColumnLabel.from_int(3, [atf.Status.UNCERTAIN]),
                ),
                LineNumber(1),
            ),
        ),
        (
            "// F K.1 1",
            ParallelFragment(
                False, MuseumNumber.of("K.1"), False, Labels(), LineNumber(1)
            ),
        ),
        (
            '// cf. L I.1 OB "my name" 1',
            ParallelText(
                True,
                TextId(Genre.LITERATURE, 1, 1),
                ChapterName(Stage.OLD_BABYLONIAN, "", "my name"),
                LineNumber(1),
            ),
        ),
        (
            '// cf. L I.1 OB "my version" "my name" 1',
            ParallelText(
                True,
                TextId(Genre.LITERATURE, 1, 1),
                ChapterName(Stage.OLD_BABYLONIAN, "my version", "my name"),
                LineNumber(1),
            ),
        ),
        (
            "// L I.1 1",
            ParallelText(False, TextId(Genre.LITERATURE, 1, 1), None, LineNumber(1)),
        ),
        (
            "// L III.10 1",
            ParallelText(False, TextId(Genre.LITERATURE, 3, 10), None, LineNumber(1)),
        ),
        (
            "// L 0.0 1",
            ParallelText(False, TextId(Genre.LITERATURE, 0, 0), None, LineNumber(1)),
        ),
        (
            "// D I.1 1",
            ParallelText(False, TextId(Genre.DIVINATION, 1, 1), None, LineNumber(1)),
        ),
        (
            "// Lex I.1 1",
            ParallelText(False, TextId(Genre.LEXICOGRAPHY, 1, 1), None, LineNumber(1)),
        ),
        (
            "// Mag III.1 2",
            ParallelText(False, TextId(Genre.MAGIC, 3, 1), None, LineNumber(2)),
        ),
        (
            "// Med I.1 1",
            ParallelText(False, TextId(Genre.MEDICINE, 1, 1), None, LineNumber(1)),
        ),
        ("// cf. (name 1)", ParallelComposition(True, "name", LineNumber(1))),
        ("// (name 1)", ParallelComposition(False, "name", LineNumber(1))),
    ],
)
def test_parse_atf_at_line(line, expected_line):
    assert parse_line(line) == expected_line
