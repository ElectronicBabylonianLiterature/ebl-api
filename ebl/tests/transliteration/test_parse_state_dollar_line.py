import pytest

from ebl.transliteration.domain import atf
from ebl.transliteration.domain.dollar_line import ScopeContainer, StateDollarLine
from ebl.transliteration.domain.atf_parsers.lark_parser import parse_atf_lark
from ebl.transliteration.domain.text import Text
from ebl.transliteration.domain.transliteration_error import TransliterationError


@pytest.mark.parametrize("prefix", ["$ ", "$"])
@pytest.mark.parametrize("parenthesis", [False, True])
@pytest.mark.parametrize(
    "line,expected_line",
    [
        (
            "2-4 lines missing",
            StateDollarLine(
                None, (2, 4), ScopeContainer(atf.Scope.LINES), atf.State.MISSING, None
            ),
        ),
        (
            "at least 1 obverse missing",
            StateDollarLine(
                atf.Qualification.AT_LEAST,
                1,
                ScopeContainer(atf.Surface.OBVERSE, ""),
                atf.State.MISSING,
                None,
            ),
        ),
        (
            "2 lines",
            StateDollarLine(None, 2, ScopeContainer(atf.Scope.LINES), None, None),
        ),
        (
            "at most 1-3 object stone blank ?",
            StateDollarLine(
                atf.Qualification.AT_MOST,
                (1, 3),
                ScopeContainer(atf.Object.OBJECT, "stone"),
                atf.State.BLANK,
                atf.DollarStatus.UNCERTAIN,
            ),
        ),
        (
            "at most 1-3 obverse",
            StateDollarLine(
                atf.Qualification.AT_MOST,
                (1, 3),
                ScopeContainer(atf.Surface.OBVERSE),
                None,
                None,
            ),
        ),
        (
            "1-3 obverse",
            StateDollarLine(
                None, (1, 3), ScopeContainer(atf.Surface.OBVERSE), None, None
            ),
        ),
        (
            "1 - 3 obverse",
            StateDollarLine(
                None, (1, 3), ScopeContainer(atf.Surface.OBVERSE), None, None
            ),
        ),
        (
            "1 obverse",
            StateDollarLine(None, 1, ScopeContainer(atf.Surface.OBVERSE), None, None),
        ),
        (
            "several obverse",
            StateDollarLine(
                None,
                atf.Extent.SEVERAL,
                ScopeContainer(atf.Surface.OBVERSE),
                None,
                None,
            ),
        ),
        (
            "several obverse blank *",
            StateDollarLine(
                None,
                atf.Extent.SEVERAL,
                ScopeContainer(atf.Surface.OBVERSE),
                atf.State.BLANK,
                atf.DollarStatus.COLLATED,
            ),
        ),
        (
            "several surface stone blank *",
            StateDollarLine(
                None,
                atf.Extent.SEVERAL,
                ScopeContainer(atf.Surface.SURFACE, "stone"),
                atf.State.BLANK,
                atf.DollarStatus.COLLATED,
            ),
        ),
        (
            "several object stone blank *",
            StateDollarLine(
                None,
                atf.Extent.SEVERAL,
                ScopeContainer(atf.Object.OBJECT, "stone"),
                atf.State.BLANK,
                atf.DollarStatus.COLLATED,
            ),
        ),
        (
            "several tablet blank *",
            StateDollarLine(
                None,
                atf.Extent.SEVERAL,
                ScopeContainer(atf.Object.TABLET),
                atf.State.BLANK,
                atf.DollarStatus.COLLATED,
            ),
        ),
        (
            "several tablet blank !",
            StateDollarLine(
                None,
                atf.Extent.SEVERAL,
                ScopeContainer(atf.Object.TABLET),
                atf.State.BLANK,
                atf.DollarStatus.EMENDED_NOT_COLLATED,
            ),
        ),
        (
            "several tablet blank !?",
            StateDollarLine(
                None,
                atf.Extent.SEVERAL,
                ScopeContainer(atf.Object.TABLET),
                atf.State.BLANK,
                atf.DollarStatus.NEEDS_COLLATION,
            ),
        ),
        (
            "1 line effaced",
            StateDollarLine(
                None, 1, ScopeContainer(atf.Scope.LINE), atf.State.EFFACED, None
            ),
        ),
        (
            "at least 1 fragment a",
            StateDollarLine(
                atf.Qualification.AT_LEAST,
                1,
                ScopeContainer(atf.Object.FRAGMENT, "a"),
                None,
                None,
            ),
        ),
        (
            "at least 1 face a",
            StateDollarLine(
                atf.Qualification.AT_LEAST,
                1,
                ScopeContainer(atf.Surface.FACE, "a"),
                None,
                None,
            ),
        ),
        (
            "at least 1 edge",
            StateDollarLine(
                atf.Qualification.AT_LEAST,
                1,
                ScopeContainer(atf.Surface.EDGE, ""),
                None,
                None,
            ),
        ),
        (
            "at least 1 edge a",
            StateDollarLine(
                atf.Qualification.AT_LEAST,
                1,
                ScopeContainer(atf.Surface.EDGE, "a"),
                None,
                None,
            ),
        ),
    ],
)
def test_parse_state_dollar_line(prefix, parenthesis, line, expected_line):
    atf_ = f"{prefix}({line})" if parenthesis else f"{prefix}{line}"
    assert parse_atf_lark(atf_).lines == Text.of_iterable([expected_line]).lines


@pytest.mark.parametrize(
    "line,expected_line",
    [
        (
            "$ (at least 1 surface thing right missing )",
            StateDollarLine(
                atf.Qualification.AT_LEAST,
                1,
                ScopeContainer(atf.Surface.SURFACE, "thing right"),
                atf.State.MISSING,
                None,
            ),
        ),
        (
            "$ (at least 1 surface thing right  )",
            StateDollarLine(
                atf.Qualification.AT_LEAST,
                1,
                ScopeContainer(atf.Surface.SURFACE, "thing right"),
                None,
                None,
            ),
        ),
        (
            "$ (at least 1 surface th(in)g  )",
            StateDollarLine(
                atf.Qualification.AT_LEAST,
                1,
                ScopeContainer(atf.Surface.SURFACE, "th(in)g"),
                None,
                None,
            ),
        ),
        (
            "$ (at least 1 surface thing  )",
            StateDollarLine(
                atf.Qualification.AT_LEAST,
                1,
                ScopeContainer(atf.Surface.SURFACE, "thing"),
                None,
                None,
            ),
        ),
        (
            "$ at least 1 surface",
            StateDollarLine(
                atf.Qualification.AT_LEAST,
                1,
                ScopeContainer(atf.Scope.SURFACE, ""),
                None,
                None,
            ),
        ),
        (
            "$ at least 1 surface missing",
            StateDollarLine(
                atf.Qualification.AT_LEAST,
                1,
                ScopeContainer(atf.Scope.SURFACE, ""),
                atf.State.MISSING,
                None,
            ),
        ),
        (
            "$ at least 1 surface wall missing",
            StateDollarLine(
                atf.Qualification.AT_LEAST,
                1,
                ScopeContainer(atf.Surface.SURFACE, "wall"),
                atf.State.MISSING,
                None,
            ),
        ),
    ],
)
def test_parse_state_dollar_line_surface_ambiguity(line, expected_line):
    assert parse_atf_lark(line).lines == Text.of_iterable([expected_line]).lines


@pytest.mark.parametrize("line", ["$ face", "$ object"])
def test_parse_state_dollar_line_invalid(line):
    with pytest.raises(TransliterationError):
        parse_atf_lark(line)
