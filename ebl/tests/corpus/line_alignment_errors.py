from typing import Callable, Sequence, Tuple

import attr

from ebl.corpus.domain.alignment import ManuscriptLineAlignment
from ebl.tests.corpus.line_annotation_kind import (
    InvalidAnnotation,
    InvalidCase,
    create_count_error,
)
from ebl.tests.corpus.line_annotation_kinds import ALIGNMENT
from ebl.tests.corpus.line_annotation_support import (
    SPECIAL_INDEX,
    LineAlignments,
    replace_item,
)
from ebl.transliteration.domain.alignment import AlignmentToken

AlignmentChange = Callable[[LineAlignments], LineAlignments]
ManuscriptPosition = Tuple[int, int]
TokenChange = Callable[[AlignmentToken], AlignmentToken]
INVALID_ALIGNMENT = "Invalid alignment"
INCOMPATIBLE_WORD_ALIGNMENT = "Incompatible alignment .* for word .*"
INCOMPATIBLE_TOKEN_ALIGNMENT = "Incompatible alignment .* for token .*"


def _change_manuscript_alignment(
    position: ManuscriptPosition,
    change: Callable[[ManuscriptLineAlignment], ManuscriptLineAlignment],
) -> AlignmentChange:
    variant_index, manuscript_index = position

    def change_alignment(alignment: LineAlignments) -> LineAlignments:
        variant = alignment[variant_index]
        return replace_item(
            alignment,
            variant_index,
            replace_item(variant, manuscript_index, change(variant[manuscript_index])),
        )

    return change_alignment


def _set_alignment_tokens(
    position: ManuscriptPosition,
    change: Callable[[Sequence[AlignmentToken]], Sequence[AlignmentToken]],
) -> AlignmentChange:
    return _change_manuscript_alignment(
        position,
        lambda manuscript: attr.evolve(
            manuscript, alignment=tuple(change(manuscript.alignment))
        ),
    )


def change_alignment_token(token_index: int, change: TokenChange) -> AlignmentChange:
    return _set_alignment_tokens(
        (0, 0),
        lambda tokens: replace_item(tokens, token_index, change(tokens[token_index])),
    )


def align(alignment: int) -> TokenChange:
    return lambda token: attr.evolve(token, alignment=alignment)


def _rename(token: AlignmentToken) -> AlignmentToken:
    return attr.evolve(token, value="nu")


ALIGNMENT_CASES: Sequence[InvalidCase[LineAlignments]] = (
    InvalidCase(
        "no variants",
        lambda alignment: (),
        create_count_error("variants", 0, 1),
        create_count_error("variants", 0, 1),
    ),
    InvalidCase(
        "extra variant",
        lambda alignment: (*alignment, alignment[0]),
        create_count_error("variants", 2, 1),
        create_count_error("variants", 2, 1),
    ),
    InvalidCase(
        "missing manuscript",
        lambda alignment: (alignment[0][:1],),
        create_count_error("manuscripts in variant 0", 1, 2),
        create_count_error("manuscripts", 1, 2),
    ),
    InvalidCase(
        "extra manuscript",
        lambda alignment: ((*alignment[0], alignment[0][0]),),
        create_count_error("manuscripts in variant 0", 3, 2),
        create_count_error("manuscripts", 3, 2),
    ),
    InvalidCase(
        "missing token",
        _set_alignment_tokens((0, 1), lambda tokens: tokens[:1]),
        create_count_error("tokens in variant 0 manuscript 1", 1, 2),
        INVALID_ALIGNMENT,
    ),
    InvalidCase(
        "extra token",
        _set_alignment_tokens((0, 1), lambda tokens: (*tokens, tokens[0])),
        create_count_error("tokens in variant 0 manuscript 1", 3, 2),
        INVALID_ALIGNMENT,
    ),
    InvalidCase(
        "token of an empty manuscript line",
        _set_alignment_tokens((0, 1), lambda _: (AlignmentToken("ku", None),)),
        create_count_error("tokens in variant 0 manuscript 1", 1, 0),
        None,
        SPECIAL_INDEX,
    ),
    InvalidCase(
        "other value",
        change_alignment_token(0, _rename),
        INCOMPATIBLE_WORD_ALIGNMENT,
        INCOMPATIBLE_WORD_ALIGNMENT,
    ),
    InvalidCase(
        "aligned word that is not alignable",
        change_alignment_token(1, align(0)),
        INCOMPATIBLE_WORD_ALIGNMENT,
        INCOMPATIBLE_WORD_ALIGNMENT,
        SPECIAL_INDEX,
    ),
    InvalidCase(
        "aligned token that is not a word",
        change_alignment_token(2, align(0)),
        INCOMPATIBLE_TOKEN_ALIGNMENT,
        INCOMPATIBLE_TOKEN_ALIGNMENT,
        SPECIAL_INDEX,
    ),
)
INVALID_ALIGNMENTS: Sequence[InvalidAnnotation] = tuple(
    map(ALIGNMENT.create_invalid, ALIGNMENT_CASES)
)
