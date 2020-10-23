from ebl.transliteration.domain.line_number import LineNumber, LineNumberRange


def test_line_number_simple():
    line_number = LineNumber(1)
    assert line_number.number == 1
    assert line_number.has_prime is False
    assert line_number.prefix_modifier is None
    assert line_number.suffix_modifier is None
    assert line_number.atf == "1."
    assert line_number.label == "1"


def test_line_number_complex():
    line_number = LineNumber(20, True, "D", "a")

    assert line_number.number == 20
    assert line_number.has_prime is True
    assert line_number.prefix_modifier == "D"
    assert line_number.suffix_modifier == "a"
    assert line_number.atf == "D+20'a."
    assert line_number.label == "D+20'a"


def test_line_number_range():
    start = LineNumber(1)
    end = LineNumber(20, True, "D", "a")
    line_number = LineNumberRange(start, end)

    assert line_number.start == start
    assert line_number.end == end
    assert line_number.atf == "1-D+20'a."
    assert line_number.label == "1-D+20'a"
