import pytest

from ebl.lemmatization.domain.lemmatization import LemmatizationToken
from ebl.transliteration.domain import atf
from ebl.transliteration.domain.at_line import (
    DiscourseAtLine,
    SurfaceAtLine,
    ColumnAtLine,
    ObjectAtLine,
    CompositeAtLine,
    HeadingAtLine,
)
from ebl.transliteration.domain.labels import SurfaceLabel, ColumnLabel, ObjectLabel
from ebl.transliteration.domain.markup import StringPart
from ebl.transliteration.domain.atf import Atf


@pytest.mark.parametrize(
    "parts,parts_text", [((), ""), ((StringPart("a"), StringPart("b c")), " ab c")]
)
def test_at_line_heading(parts, parts_text) -> None:
    at_line = HeadingAtLine(1, parts)

    assert at_line.atf == Atf(f"@h1{parts_text}")
    assert at_line.lemmatization == (LemmatizationToken(f"h1{parts_text}"),)
    assert at_line.display_value == f"h1{parts_text}"


def test_at_line_column() -> None:
    at_line = ColumnAtLine(ColumnLabel.from_int(1, (atf.Status.COLLATION,)))

    assert at_line.lemmatization == (LemmatizationToken("column 1*"),)
    assert at_line.display_value == "column 1*"


def test_at_line_column_no_status() -> None:
    at_line = ColumnAtLine(ColumnLabel.from_int(1))

    assert at_line.lemmatization == (LemmatizationToken("column 1"),)
    assert at_line.display_value == "column 1"


def test_at_line_discourse() -> None:
    at_line = DiscourseAtLine(atf.Discourse.SIGNATURES)

    assert at_line.lemmatization == (LemmatizationToken("signatures"),)
    assert at_line.discourse_label == atf.Discourse.SIGNATURES
    assert at_line.display_value == "signatures"


def test_at_line_surface() -> None:
    at_line = SurfaceAtLine(
        SurfaceLabel((atf.Status.CORRECTION,), atf.Surface.SURFACE, "Stone wig")
    )

    assert at_line.lemmatization == (LemmatizationToken("surface Stone wig!"),)
    assert at_line.surface_label == SurfaceLabel(
        (atf.Status.CORRECTION,), atf.Surface.SURFACE, "Stone wig"
    )
    assert at_line.display_value == "surface Stone wig!"


def test_at_line_surface_no_status() -> None:
    at_line = SurfaceAtLine(SurfaceLabel([], atf.Surface.SURFACE, "Stone wig"))

    assert at_line.lemmatization == (LemmatizationToken("surface Stone wig"),)
    assert at_line.surface_label == SurfaceLabel([], atf.Surface.SURFACE, "Stone wig")
    assert at_line.display_value == "surface Stone wig"


def test_at_line_surface_instantiate_text_with_wrong_surface() -> None:
    with pytest.raises(ValueError):  # pyre-ignore[16]
        at_line = SurfaceAtLine(
            SurfaceLabel((atf.Status.CORRECTION,), atf.Surface.OBVERSE, "Stone wig")
        )
        assert at_line.lemmatization == (LemmatizationToken("obverse Stone wig!"),)
        assert at_line.surface_label == SurfaceLabel(
            (atf.Status.CORRECTION,), atf.Surface.OBVERSE, "Stone wig"
        )
        assert at_line.display_value == "obverse Stone wig!"


def test_at_line_object_no_status() -> None:
    at_line = ObjectAtLine(ObjectLabel([], atf.Object.OBJECT, "Stone wig"))

    assert at_line.lemmatization == (LemmatizationToken("object Stone wig"),)
    assert at_line.label == ObjectLabel([], atf.Object.OBJECT, "Stone wig")
    assert at_line.display_value == "object Stone wig"


def test_at_line_object() -> None:
    at_line = ObjectAtLine(
        ObjectLabel([atf.Status.CORRECTION], atf.Object.OBJECT, "Stone wig")
    )
    assert at_line.lemmatization == (LemmatizationToken("object Stone wig!"),)
    assert at_line.label == ObjectLabel(
        [atf.Status.CORRECTION], atf.Object.OBJECT, "Stone wig"
    )
    assert at_line.display_value == "object Stone wig!"


def test_at_line_composite() -> None:
    at_line = CompositeAtLine(atf.Composite.DIV, "paragraph", 1)

    assert at_line.lemmatization == (LemmatizationToken("div paragraph 1"),)
    assert at_line.composite == atf.Composite.DIV
    assert at_line.text == "paragraph"
    assert at_line.number == 1
    assert at_line.display_value == "div paragraph 1"


def test_at_line_composite_constant() -> None:
    at_line = CompositeAtLine(atf.Composite.COMPOSITE, "")

    assert at_line.lemmatization == (LemmatizationToken("composite"),)
    assert at_line.composite == atf.Composite.COMPOSITE
    assert at_line.text == ""
    assert at_line.number is None
    assert at_line.display_value == "composite"


def test_at_line_composite_milestone() -> None:
    at_line = CompositeAtLine(atf.Composite.MILESTONE, "o", 1)

    assert at_line.lemmatization == (LemmatizationToken("m=locator o 1"),)
    assert at_line.composite == atf.Composite.MILESTONE
    assert at_line.text == "o"
    assert at_line.number == 1
    assert at_line.display_value == "m=locator o 1"


def test_at_line_composite_raise_error() -> None:
    with pytest.raises(ValueError):  # pyre-ignore[16]
        CompositeAtLine(atf.Composite.END, "paragraph", 1)
