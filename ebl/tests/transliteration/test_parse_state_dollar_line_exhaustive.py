import pytest

from ebl.transliteration.domain import atf
from ebl.transliteration.domain.dollar_line import ScopeContainer, StateDollarLine
from ebl.transliteration.domain.atf_parsers.lark_parser import parse_atf_lark
from ebl.transliteration.domain.text import Text


pytest.skip(
    "Very large number of tests. Run only when making changes to the dollar line.",
    allow_module_level=True,
)


QUALIFICATIONS = [
    ("at least", atf.Qualification.AT_LEAST),
    ("at most", atf.Qualification.AT_MOST),
    ("about", atf.Qualification.ABOUT),
]

EXTENTS = [
    ("145", 145),
    ("143-533", (143, 533)),
    ("143 - 533", (143, 533)),
    ("several", atf.Extent.SEVERAL),
    ("some", atf.Extent.SOME),
    ("rest of", atf.Extent.REST_OF),
    ("start of", atf.Extent.START_OF),
    ("beginning of", atf.Extent.BEGINNING_OF),
    ("middle of", atf.Extent.MIDDLE_OF),
    ("end of", atf.Extent.END_OF),
]

SCOPES = [
    ("obverse", ScopeContainer(atf.Surface.OBVERSE)),
    ("reverse", ScopeContainer(atf.Surface.REVERSE)),
    ("bottom", ScopeContainer(atf.Surface.BOTTOM)),
    ("edge", ScopeContainer(atf.Surface.EDGE)),
    ("left", ScopeContainer(atf.Surface.LEFT)),
    ("right", ScopeContainer(atf.Surface.RIGHT)),
    ("top", ScopeContainer(atf.Surface.TOP)),
    ("surface thing right", ScopeContainer(atf.Surface.SURFACE, "thing right")),
    ("surface th(in)g", ScopeContainer(atf.Surface.SURFACE, "th(in)g")),
    ("edge a", ScopeContainer(atf.Surface.EDGE, "a")),
    ("face z", ScopeContainer(atf.Surface.FACE, "z")),
    ("tablet", ScopeContainer(atf.Object.TABLET)),
    ("envelope", ScopeContainer(atf.Object.ENVELOPE)),
    ("prism", ScopeContainer(atf.Object.PRISM)),
    ("bulla", ScopeContainer(atf.Object.BULLA)),
    ("fragment a thing", ScopeContainer(atf.Object.FRAGMENT, "a thing")),
    ("object stone", ScopeContainer(atf.Object.OBJECT, "stone")),
    ("object stone thing", ScopeContainer(atf.Object.OBJECT, "stone thing")),
    ("column", ScopeContainer(atf.Scope.COLUMN)),
    ("line", ScopeContainer(atf.Scope.LINE)),
    ("lines", ScopeContainer(atf.Scope.LINES)),
    ("case", ScopeContainer(atf.Scope.CASE)),
    ("cases", ScopeContainer(atf.Scope.CASES)),
    ("side", ScopeContainer(atf.Scope.SIDE)),
    ("excerpt", ScopeContainer(atf.Scope.EXCERPT)),
    ("surface", ScopeContainer(atf.Scope.SURFACE)),
]

STATES = [
    ("blank", atf.State.BLANK),
    ("broken", atf.State.BROKEN),
    ("illegible", atf.State.ILLEGIBLE),
    ("missing", atf.State.MISSING),
    ("traces", atf.State.TRACES),
    ("omitted", atf.State.OMITTED),
    ("continues", atf.State.CONTINUES),
    ("effaced", atf.State.EFFACED),
]

STATUSES = [
    ("*", atf.DollarStatus.COLLATED),
    ("!", atf.DollarStatus.EMENDED_NOT_COLLATED),
    ("?", atf.DollarStatus.UNCERTAIN),
    ("!?", atf.DollarStatus.NEEDS_COLLATION),
    ("°", atf.DollarStatus.NO_LONGER_VISIBLE),
]


@pytest.mark.parametrize("qualification,expected_qualification", QUALIFICATIONS)
def test_qualification(qualification, expected_qualification):
    line = f"$ {qualification}"
    expected_line = StateDollarLine(expected_qualification, None, None, None, None)
    assert parse_atf_lark(line).lines == Text.of_iterable([expected_line]).lines


@pytest.mark.parametrize("extent,expected_extent", EXTENTS)
def test_extent(extent, expected_extent):
    line = f"$ {extent}"
    expected_line = StateDollarLine(None, expected_extent, None, None, None)
    assert parse_atf_lark(line).lines == Text.of_iterable([expected_line]).lines


@pytest.mark.parametrize("scope,expected_scope", SCOPES)
def test_scope(scope, expected_scope):
    line = f"$ {scope}"
    expected_line = StateDollarLine(None, None, expected_scope, None, None)
    assert parse_atf_lark(line).lines == Text.of_iterable([expected_line]).lines


@pytest.mark.parametrize("state,expected_state", STATES)
def test_state(state, expected_state):
    line = f"$ {state}"
    expected_line = StateDollarLine(None, None, None, expected_state, None)
    assert parse_atf_lark(line).lines == Text.of_iterable([expected_line]).lines


@pytest.mark.parametrize("status,expected_status", STATUSES)
def test_status(status, expected_status):
    line = f"$ {status}"
    expected_line = StateDollarLine(None, None, None, None, expected_status)
    assert parse_atf_lark(line).lines == Text.of_iterable([expected_line]).lines


@pytest.mark.parametrize("qualification,expected_qualification", QUALIFICATIONS)
@pytest.mark.parametrize("extent,expected_extent", EXTENTS)
@pytest.mark.parametrize("scope,expected_scope", SCOPES)
@pytest.mark.parametrize("state,expected_state", STATES)
@pytest.mark.parametrize("status,expected_status", STATUSES)
def test_combinations(
    qualification,
    extent,
    scope,
    state,
    status,
    expected_qualification,
    expected_extent,
    expected_scope,
    expected_state,
    expected_status,
):
    line = " ".join(["$", qualification, extent, scope, state, status])
    expected_line = StateDollarLine(
        expected_qualification,
        expected_extent,
        expected_scope,
        expected_state,
        expected_status,
    )
    assert parse_atf_lark(line).lines == Text.of_iterable([expected_line]).lines
