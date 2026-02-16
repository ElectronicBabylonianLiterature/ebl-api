import pytest

from ebl.corpus.domain.chapter import Stage
from ebl.transliteration.domain.text_id import TextId
from ebl.transliteration.domain.museum_number import MuseumNumber
from ebl.lemmatization.domain.lemmatization import LemmatizationToken
from ebl.transliteration.domain.atf import Atf, Status, Surface
from ebl.transliteration.domain.genre import Genre
from ebl.transliteration.domain.labels import SurfaceLabel
from ebl.transliteration.domain.line_number import LineNumber
from ebl.transliteration.domain.parallel_line import (
    ChapterName,
    Labels,
    ParallelComposition,
    ParallelFragment,
    ParallelText,
)


@pytest.mark.parametrize(
    "cf,duplicates,labels,display_value",
    [
        (
            True,
            True,
            Labels(surface=SurfaceLabel((Status.CORRECTION,), Surface.OBVERSE)),
            "cf. F K.1 &d o! 1",
        ),
        (False, False, Labels(), "F K.1 1"),
    ],
)
def test_parallel_fragment(cf, duplicates, labels, display_value) -> None:
    museum_number = MuseumNumber.of("K.1")
    line_number = LineNumber(1)
    line = ParallelFragment(cf, museum_number, duplicates, labels, line_number)

    assert line.has_cf is cf
    assert line.museum_number == museum_number
    assert line.has_duplicates is duplicates
    assert line.labels == labels
    assert line.line_number == line_number

    assert line.display_value == display_value
    assert line.atf == Atf(f"// {display_value}")
    assert line.lemmatization == (LemmatizationToken(display_value),)


@pytest.mark.parametrize(
    "cf,chapter,display_value",
    [
        (
            True,
            ChapterName(Stage.OLD_BABYLONIAN, "my version", "my name"),
            'cf. L I.1 OB "my version" "my name" 1',
        ),
        (
            False,
            ChapterName(Stage.OLD_BABYLONIAN, "", "my name"),
            'L I.1 OB "my name" 1',
        ),
        (False, None, "L I.1 1"),
    ],
)
def test_parallel_text(cf, chapter, display_value) -> None:
    text_id = TextId(Genre.LITERATURE, 1, 1)
    line_number = LineNumber(1)
    line = ParallelText(cf, text_id, chapter, line_number)

    assert line.has_cf is cf
    assert line.text == text_id
    assert line.chapter == chapter
    assert line.line_number == line_number

    assert line.display_value == display_value
    assert line.atf == Atf(f"// {display_value}")
    assert line.lemmatization == (LemmatizationToken(display_value),)


@pytest.mark.parametrize(
    "cf,display_value", [(True, "cf. (my name 1)"), (False, "(my name 1)")]
)
def test_parallel_composition(cf, display_value) -> None:
    name = "my name"
    line_number = LineNumber(1)
    line = ParallelComposition(cf, name, line_number)

    assert line.has_cf is cf
    assert line.name == name
    assert line.line_number == line_number

    assert line.display_value == display_value
    assert line.atf == Atf(f"// {display_value}")
    assert line.lemmatization == (LemmatizationToken(display_value),)
