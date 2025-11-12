from typing import Sequence, Iterable
from lark.visitors import Transformer, v_args, Token
from ebl.transliteration.domain.labels import (
    Label,
    ColumnLabel,
    ObjectLabel,
    SurfaceLabel,
)
from ebl.transliteration.domain.line_number import LineNumber, LineNumberRange
from ebl.transliteration.domain.atf import Object, Status, Surface

PREFIXES = [
    "ebl_atf_at_line",
    "ebl_atf_text_line",
    "ebl_atf_translation_line",
    "ebl_atf_parallel_line",
    "ebl_atf_manuscript_line",
]


class CommonTransformer(Transformer):
    def __init__(self):
        super().__init__()
        for method in [method for method in dir(self) if "ebl_atf_common" in method]:
            _method = method.replace("ebl_atf_common", "")
            setattr(self, method.replace("ebl_atf_common__", ""), getattr(self, method))
            for prefix in PREFIXES:
                setattr(self, f"{prefix}__{method}", getattr(self, method))
                setattr(self, f"{prefix}{_method}", getattr(self, method))

    @v_args(inline=True)
    def ebl_atf_common__INT(self, number) -> int:
        return int(number)

    @v_args(inline=True)
    def ebl_atf_common__single_line_number(
        self, prefix_modifier, number, prime, suffix_modifier
    ) -> LineNumber:
        prefix_modifier = str(prefix_modifier) if prefix_modifier else None
        suffix_modifier = str(suffix_modifier) if suffix_modifier else None
        return LineNumber(
            int(number), prime is not None, prefix_modifier, suffix_modifier
        )

    @v_args(inline=True)
    def ebl_atf_common__legacy_prefixed_single_line_number(
        self, prefix_modifier, number, prime, suffix_modifier
    ) -> LineNumber:
        prefix_modifier = str(prefix_modifier) if prefix_modifier else None
        suffix_modifier = str(suffix_modifier) if suffix_modifier else None
        return LineNumber(
            int(number), prime is not None, prefix_modifier, suffix_modifier
        )

    @v_args(inline=True)
    def ebl_atf_common__line_number_range(self, start, end) -> LineNumberRange:
        return LineNumberRange(start, end)

    def ebl_atf_common__labels(self, children) -> Sequence[Label]:
        return tuple(children)

    @v_args(inline=True)
    def ebl_atf_common__column_label(
        self, numeral: Token, status: Sequence[Status]
    ) -> ColumnLabel:
        return ColumnLabel.from_label(numeral, status)  # pyre-ignore[6]

    @v_args(inline=True)
    def ebl_atf_common__surface_label(
        self, surface: Token, status: Sequence[Status]
    ) -> SurfaceLabel:
        return SurfaceLabel.from_label(
            Surface.from_label(surface),  # pyre-ignore[6]
            status,
        )

    @v_args(inline=True)
    def ebl_atf_common__object_label(
        self, object_: Token, status: Sequence[Status]
    ) -> ObjectLabel:
        return ObjectLabel.from_object(Object(object_), status)

    def ebl_atf_common__status(self, children: Iterable[Token]) -> Sequence[Status]:
        return tuple(Status(token) for token in children)
