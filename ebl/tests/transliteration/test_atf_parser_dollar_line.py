import pytest

from ebl.transliteration.domain import atf
from ebl.transliteration.domain.lark_parser import parse_atf_lark
from ebl.transliteration.domain.dollar_line import (
    LooseDollarLine,
    ImageDollarLine,
    RulingDollarLine,
    ScopeContainer,
    StateDollarLine,
)
from ebl.transliteration.domain.text import Text


@pytest.mark.parametrize("parser", [parse_atf_lark])
@pytest.mark.parametrize(
    "line,expected_tokens",
    [
        (
            "$ (end of side)",
            [
                StateDollarLine(
                    None,
                    atf.Extent.END_OF,
                    ScopeContainer(atf.Scope.SIDE, ""),
                    None,
                    None,
                )
            ],
        ),
        ("$ (image 1a = great )", [ImageDollarLine("1", "a", "great")]),
        (
            "$ (image 1 = numbered diagram of triangle)",
            [ImageDollarLine("1", None, "numbered diagram of triangle")],
        ),
        ("$ single ruling", [RulingDollarLine(atf.Ruling.SINGLE)]),
        ("$ double ruling", [RulingDollarLine(atf.Ruling.DOUBLE)]),
        ("$ triple ruling", [RulingDollarLine(atf.Ruling.TRIPLE)]),
    ],
)
def test_parse_atf_dollar_ruling_and_image(parser, line, expected_tokens):
    assert parser(line).lines == Text.of_iterable(expected_tokens).lines


@pytest.mark.parametrize("parser", [parse_atf_lark])
@pytest.mark.parametrize(
    "line,expected_tokens",
    [
        (
            "$ at least 1 obverse missing",
            [
                StateDollarLine(
                    atf.Qualification.AT_LEAST,
                    1,
                    ScopeContainer(atf.Surface.OBVERSE, ""),
                    atf.State.MISSING,
                    None,
                )
            ],
        ),
        (
            "$ 2 lines",
            [StateDollarLine(None, 2, ScopeContainer(atf.Scope.LINES), None, None,)],
        ),
        (
            "$ at most 1-3 object stone blank ?",
            [
                StateDollarLine(
                    atf.Qualification.AT_MOST,
                    (1, 3),
                    ScopeContainer(atf.Object.OBJECT, "stone"),
                    atf.State.BLANK,
                    atf.Status.UNCERTAIN,
                )
            ],
        ),
        (
            "$ at most 1-3 obverse",
            [
                StateDollarLine(
                    atf.Qualification.AT_MOST,
                    (1, 3),
                    ScopeContainer(atf.Surface.OBVERSE),
                    None,
                    None,
                )
            ],
        ),
        (
            "$ 1-3 obverse",
            [
                StateDollarLine(
                    None, (1, 3), ScopeContainer(atf.Surface.OBVERSE), None, None,
                )
            ],
        ),
        (
            "$ 1 - 3 obverse",
            [
                StateDollarLine(
                    None, (1, 3), ScopeContainer(atf.Surface.OBVERSE), None, None,
                )
            ],
        ),
        (
            "$ 1 obverse",
            [
                StateDollarLine(
                    None, 1, ScopeContainer(atf.Surface.OBVERSE), None, None,
                )
            ],
        ),
        (
            "$ several obverse",
            [
                StateDollarLine(
                    None,
                    atf.Extent.SEVERAL,
                    ScopeContainer(atf.Surface.OBVERSE),
                    None,
                    None,
                )
            ],
        ),
        (
            "$ several obverse",
            [
                StateDollarLine(
                    None,
                    atf.Extent.SEVERAL,
                    ScopeContainer(atf.Surface.OBVERSE),
                    None,
                    None,
                )
            ],
        ),
        (
            "$ several obverse",
            [
                StateDollarLine(
                    None,
                    atf.Extent.SEVERAL,
                    ScopeContainer(atf.Surface.OBVERSE),
                    None,
                    None,
                )
            ],
        ),
        (
            "$ several obverse blank *",
            [
                StateDollarLine(
                    None,
                    atf.Extent.SEVERAL,
                    ScopeContainer(atf.Surface.OBVERSE),
                    atf.State.BLANK,
                    atf.Status.COLLATION,
                )
            ],
        ),
        (
            "$ several surface stone blank *",
            [
                StateDollarLine(
                    None,
                    atf.Extent.SEVERAL,
                    ScopeContainer(atf.Surface.SURFACE, "stone"),
                    atf.State.BLANK,
                    atf.Status.COLLATION,
                )
            ],
        ),
        (
            "$ several object stone blank *",
            [
                StateDollarLine(
                    None,
                    atf.Extent.SEVERAL,
                    ScopeContainer(atf.Object.OBJECT, "stone"),
                    atf.State.BLANK,
                    atf.Status.COLLATION,
                )
            ],
        ),
        (
            "$ several tablet blank *",
            [
                StateDollarLine(
                    None,
                    atf.Extent.SEVERAL,
                    ScopeContainer(atf.Object.TABLET),
                    atf.State.BLANK,
                    atf.Status.COLLATION,
                )
            ],
        ),
        (
            "$ several tablet blank !",
            [
                StateDollarLine(
                    None,
                    atf.Extent.SEVERAL,
                    ScopeContainer(atf.Object.TABLET),
                    atf.State.BLANK,
                    atf.Status.CORRECTION,
                )
            ],
        ),
        (
            "$ several tablet blank ?",
            [
                StateDollarLine(
                    None,
                    atf.Extent.SEVERAL,
                    ScopeContainer(atf.Object.TABLET),
                    atf.State.BLANK,
                    atf.Status.UNCERTAIN,
                )
            ],
        ),
    ],
)
def test_parse_atf_state_dollar_line(parser, line, expected_tokens):
    assert parser(line).lines == Text.of_iterable(expected_tokens).lines


@pytest.mark.parametrize("parser", [parse_atf_lark])
@pytest.mark.parametrize(
    "line,expected_tokens",
    [
        ("$ (single ruling)", [RulingDollarLine(atf.Ruling.SINGLE)],),
        ("$ (aa dd )", [LooseDollarLine("aa dd")],),
        (
            "$ (at least 1 obverse missing)",
            [
                StateDollarLine(
                    atf.Qualification.AT_LEAST,
                    1,
                    ScopeContainer(atf.Surface.OBVERSE, ""),
                    atf.State.MISSING,
                    None,
                )
            ],
        ),
    ],
)
def test_parse_atf_loose_to_strict_dollar_line(parser, line, expected_tokens):
    assert parser(line).lines == Text.of_iterable(expected_tokens).lines


@pytest.mark.parametrize("parser", [parse_atf_lark])
@pytest.mark.parametrize(
    "line,expected_tokens",
    [
        (
            "$ (at least 1 surface thing right missing )",
            [
                StateDollarLine(
                    atf.Qualification.AT_LEAST,
                    1,
                    ScopeContainer(atf.Surface.SURFACE, "thing right"),
                    atf.State.MISSING,
                    None,
                )
            ],
        ),
        (
            "$ (at least 1 surface thing right  )",
            [
                StateDollarLine(
                    atf.Qualification.AT_LEAST,
                    1,
                    ScopeContainer(atf.Surface.SURFACE, "thing right"),
                    None,
                    None,
                )
            ],
        ),
        (
            "$ (at least 1 surface th(in)g  )",
            [
                StateDollarLine(
                    atf.Qualification.AT_LEAST,
                    1,
                    ScopeContainer(atf.Surface.SURFACE, "th(in)g"),
                    None,
                    None,
                )
            ],
        ),
        (
            "$ (at least 1 surface thing  )",
            [
                StateDollarLine(
                    atf.Qualification.AT_LEAST,
                    1,
                    ScopeContainer(atf.Surface.SURFACE, "thing"),
                    None,
                    None,
                )
            ],
        ),
        (
            "$ at least 1 surface",
            [
                StateDollarLine(
                    atf.Qualification.AT_LEAST,
                    1,
                    ScopeContainer(atf.Scope.SURFACE, ""),
                    None,
                    None,
                )
            ],
        ),
        (
            "$ at least 1 surface missing",
            [
                StateDollarLine(
                    atf.Qualification.AT_LEAST,
                    1,
                    ScopeContainer(atf.Scope.SURFACE, ""),
                    atf.State.MISSING,
                    None,
                )
            ],
        ),
        (
            "$ at least 1 surface wall missing",
            [
                StateDollarLine(
                    atf.Qualification.AT_LEAST,
                    1,
                    ScopeContainer(atf.Surface.SURFACE, "wall"),
                    atf.State.MISSING,
                    None,
                )
            ],
        ),
    ],
)
def test_parse_atf_surface_ambiguity_dollar_line(parser, line, expected_tokens):
    assert parser(line).lines == Text.of_iterable(expected_tokens).lines


@pytest.mark.parametrize("parser", [parse_atf_lark])
@pytest.mark.parametrize(
    "line,expected_tokens",
    [
        (
            "$ at least 1 fragment a",
            [
                StateDollarLine(
                    atf.Qualification.AT_LEAST,
                    1,
                    ScopeContainer(atf.Object.FRAGMENT, "a"),
                    None,
                    None,
                )
            ],
        ),
    ],
)
def test_parse_atf_fragment_object_dollar_line(parser, line, expected_tokens):
    assert parser(line).lines == Text.of_iterable(expected_tokens).lines


@pytest.mark.parametrize("parser", [parse_atf_lark])
@pytest.mark.parametrize(
    "line,expected_tokens",
    [
        (
            "$ at least 1 face a",
            [
                StateDollarLine(
                    atf.Qualification.AT_LEAST,
                    1,
                    ScopeContainer(atf.Surface.FACE, "a"),
                    None,
                    None,
                )
            ],
        ),
    ],
)
def test_parse_atf_face_surface_dollar_line(parser, line, expected_tokens):
    assert parser(line).lines == Text.of_iterable(expected_tokens).lines


@pytest.mark.parametrize("parser", [parse_atf_lark])
@pytest.mark.parametrize(
    "line,expected_tokens",
    [
        (
            "$ at least 1 edge",
            [
                StateDollarLine(
                    atf.Qualification.AT_LEAST,
                    1,
                    ScopeContainer(atf.Surface.EDGE, ""),
                    None,
                    None,
                )
            ],
        ),
        (
            "$ at least 1 edge a",
            [
                StateDollarLine(
                    atf.Qualification.AT_LEAST,
                    1,
                    ScopeContainer(atf.Surface.EDGE, "a"),
                    None,
                    None,
                )
            ],
        ),
    ],
)
def test_parse_atf_edge_surface_dollar_line(parser, line, expected_tokens):
    assert parser(line).lines == Text.of_iterable(expected_tokens).lines
