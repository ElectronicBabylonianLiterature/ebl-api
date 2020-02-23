from ebl.transliteration.domain import atf
from ebl.transliteration.domain.at_line import AtLine, Heading
from ebl.transliteration.domain.tokens import ValueToken


def test_at_line_signatures():
    at_line = AtLine(atf.Discourse.SIGNATURES, None, "")

    assert at_line.prefix == "@"
    assert at_line.content == (ValueToken(" signatures"),)
    assert at_line.structural_tag == atf.Discourse.SIGNATURES
    assert at_line.status == None
    assert at_line.text == ""


def test_at_line_headings():
    at_line = AtLine(Heading(1), atf.Status.CORRECTION, "")

    assert at_line.prefix == "@"
    assert at_line.content == (ValueToken(" h1 !"),)
    assert at_line.structural_tag == Heading(1)
    assert at_line.status == atf.Status.CORRECTION
    assert at_line.text == ""


def test_at_line_object():
    at_line = AtLine(atf.Object.OBJECT, atf.Status.CORRECTION, "Stone wig")

    assert at_line.prefix == "@"
    assert at_line.content == (ValueToken(" object Stone wig !"),)
    assert at_line.structural_tag == atf.Object.OBJECT
    assert at_line.status == atf.Status.CORRECTION
    assert at_line.text == "Stone wig"


def test_at_line_surface():
    at_line = AtLine(atf.Surface.SURFACE, atf.Status.CORRECTION, "Stone wig")

    assert at_line.prefix == "@"
    assert at_line.content == (ValueToken(" surface Stone wig !"),)
    assert at_line.structural_tag == atf.Surface.SURFACE
    assert at_line.status == atf.Status.CORRECTION
    assert at_line.text == "Stone wig"
