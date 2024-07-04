from lark.visitors import Transformer, v_args

from ebl.transliteration.domain import atf
from ebl.transliteration.domain.dollar_line import (
    LooseDollarLine,
    ImageDollarLine,
    RulingDollarLine,
    ScopeContainer,
    StateDollarLine,
    SealDollarLine,
)


class DollarLineTransformer(Transformer):
    def ebl_atf_dollar_line__free_text(self, content):
        return "".join(content)

    @v_args(inline=True)
    def ebl_atf_dollar_line__loose(self, content):
        return LooseDollarLine(str(content))

    @v_args(inline=True)
    def ebl_atf_dollar_line__ruling(self, number=1, status=None):
        return RulingDollarLine(atf.Ruling(str(number)), status)

    @v_args(inline=True)
    def ebl_atf_dollar_line__image(self, number, letter, text):
        return ImageDollarLine(str(number), letter and str(letter), text)

    @v_args(inline=True)
    def ebl_atf_dollar_line__seal(self, number):
        return SealDollarLine(number)

    @v_args(inline=True)
    def ebl_atf_dollar_line__DOLLAR_STATUS(self, status):
        return atf.DollarStatus(str(status))

    @v_args(inline=True)
    def ebl_atf_dollar_line__STATE(self, state):
        return atf.State(str(state))

    @v_args(inline=True)
    def ebl_atf_dollar_line__OBJECT(self, object):
        return ScopeContainer(atf.Object(object))

    @v_args(inline=True)
    def ebl_atf_dollar_line__generic_object(self, text):
        return ScopeContainer(atf.Object.OBJECT, str(text))

    @v_args(inline=True)
    def ebl_atf_dollar_line__fragment(self, text):
        return ScopeContainer(atf.Object.FRAGMENT, str(text))

    @v_args(inline=True)
    def ebl_atf_dollar_line__SURFACE(self, surface):
        return ScopeContainer(atf.Surface.from_atf(str(surface)))

    @v_args(inline=True)
    def ebl_atf_dollar_line__generic_surface(self, text):
        return ScopeContainer(atf.Surface.SURFACE, str(text))

    @v_args(inline=True)
    def ebl_atf_dollar_line__face(self, text):
        return ScopeContainer(atf.Surface.FACE, str(text))

    @v_args(inline=True)
    def ebl_atf_dollar_line__edge(self, text=""):
        return ScopeContainer(atf.Surface.EDGE, str(text))

    @v_args(inline=True)
    def ebl_atf_dollar_line__SCOPE(self, scope):
        return ScopeContainer(atf.Scope(str(scope)))

    @v_args(inline=True)
    def ebl_atf_dollar_line__EXTENT(self, extent):
        return atf.Extent(str(extent))

    @v_args(inline=True)
    def ebl_atf_dollar_line__INT(self, number):
        return int(number)

    @v_args(inline=True)
    def ebl_atf_dollar_line__range(self, number1, number2):
        return (number1, number2)

    @v_args(inline=True)
    def ebl_atf_dollar_line__QUALIFICATION(self, qualification):
        return atf.Qualification(str(qualification))

    @v_args(inline=True)
    def ebl_atf_dollar_line__state(
        self, qualification, extent=None, scope_container=None, state=None, status=None
    ):
        return StateDollarLine(qualification, extent, scope_container, state, status)

    @v_args(inline=True)
    def ebl_atf_dollar_line__state_extent(
        self, extent, scope_container=None, state=None, status=None
    ):
        return StateDollarLine(None, extent, scope_container, state, status)

    @v_args(inline=True)
    def ebl_atf_dollar_line__state_scope(
        self, scope_container, state=None, status=None
    ):
        return StateDollarLine(None, None, scope_container, state, status)

    @v_args(inline=True)
    def ebl_atf_dollar_line__state_state(self, state, status):
        return StateDollarLine(None, None, None, state, status)

    @v_args(inline=True)
    def ebl_atf_dollar_line__state_status(self, status):
        return StateDollarLine(None, None, None, None, status)
