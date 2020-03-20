from lark.visitors import Transformer, v_args

from ebl.transliteration.domain import atf
from ebl.transliteration.domain.at_line import (
    SealAtLine,
    ColumnAtLine,
    HeadingAtLine,
    DiscourseAtLine,
    SurfaceAtLine,
    ObjectAtLine,
    DivisionAtLine,
    CompositeAtLine,
)
from ebl.transliteration.domain.labels import ColumnLabel, SurfaceLabel


class AtLineTransformer(Transformer):
    def ebl_atf_at_line__free_text(self, content):
        return "".join(content).rstrip(" ")

    @v_args(inline=True)
    def ebl_atf_at_line__INT(self, number):
        return int(number)

    @v_args(inline=True)
    def ebl_atf_at_line__LCASE_LETTER(self, letter):
        return str(letter)

    @v_args(inline=True)
    def ebl_atf_at_line__STATUS(self, status):
        return atf.Status(status)

    @v_args(inline=True)
    def ebl_atf_at_line__seal(self, number):
        return SealAtLine(number)

    @v_args(inline=True)
    def ebl_atf_at_line__column(self, number, statuses):
        return ColumnAtLine(ColumnLabel.from_int(number, statuses.children))

    @v_args(inline=True)
    def ebl_atf_at_line__discourse(self, discourse):
        return DiscourseAtLine(atf.Discourse(discourse))

    @v_args(inline=True)
    def ebl_atf_at_line__heading(self, number):
        return HeadingAtLine(number)

    @v_args(inline=True)
    def ebl_atf_at_line__OBJECT(self, object):
        return (atf.Object(object),)

    @v_args(inline=True)
    def ebl_atf_at_line__generic_object(self, text):
        return (
            atf.Object.OBJECT,
            str(text),
        )

    @v_args(inline=True)
    def ebl_atf_at_line__fragment(self, text):
        return (atf.Object.FRAGMENT,)

    @v_args(inline=True)
    def ebl_atf_at_line__SURFACE(self, surface):
        return (atf.Surface.from_atf(str(surface)),)

    @v_args(inline=True)
    def ebl_atf_at_line__generic_surface(self, text):
        return atf.Surface.SURFACE, str(text)

    @v_args(inline=True)
    def ebl_atf_at_line__face(self, text):
        return atf.Surface.FACE, str(text)

    @v_args(inline=True)
    def ebl_atf_at_line__edge(self, text=""):
        return atf.Surface.EDGE, str(text)

    @v_args(inline=True)
    def ebl_atf_at_line__surface_with_status(self, surface, statuses):
        if len(surface) == 2:
            return SurfaceAtLine(
                SurfaceLabel(statuses.children, surface[0], surface[1])
            )
        else:
            return SurfaceAtLine(SurfaceLabel(statuses.children, surface[0]))

    @v_args(inline=True)
    def ebl_atf_at_line__object_with_status(self, object, statuses):
        if len(object) == 2:
            return ObjectAtLine(statuses.children, object[0], object[1],)
        else:
            return ObjectAtLine(statuses.children, object[0])

    @v_args(inline=True)
    def ebl_atf_at_line__divisions(self, text, digit):
        return DivisionAtLine(text, digit)

    @v_args(inline=True)
    def ebl_atf_at_line__composite_start(self, text, number):
        return CompositeAtLine(atf.Composite.DIV, text, number)

    @v_args(inline=True)
    def ebl_atf_at_line__composite_end(self, text):
        return CompositeAtLine(atf.Composite.END, text)
