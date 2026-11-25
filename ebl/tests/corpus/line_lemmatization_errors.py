import re
from typing import Callable, Sequence

import attr

from ebl.corpus.application.lemmatization import LineVariantLemmatization
from ebl.dictionary.domain.word import WordId
from ebl.lemmatization.domain.lemmatization import LemmatizationToken
from ebl.tests.corpus.line_annotation_kind import (
    InvalidAnnotation,
    InvalidCase,
    create_count_error,
)
from ebl.tests.corpus.line_annotation_kinds import LEMMATIZATION
from ebl.tests.corpus.line_annotation_support import (
    SPECIAL_INDEX,
    LineLemmatizations,
    replace_item,
)

__all__ = ("INVALID_LEMMATIZATIONS",)

LemmatizationChange = Callable[[LineLemmatizations], LineLemmatizations]
TokenChange = Callable[[LemmatizationToken], LemmatizationToken]
INVALID_LEMMATIZATION = "Invalid lemmatization"
INCOMPATIBLE_WORD_LEMMA = "Cannot apply .* to .*"
INCOMPATIBLE_TOKEN_LEMMA = "Incompatible lemmatization token .* for .*"
ANY_LEMMA = (WordId("aklu I"),)


def _change_first_variant(
    change: Callable[[LineVariantLemmatization], LineVariantLemmatization],
) -> LemmatizationChange:
    return lambda lemmatization: replace_item(
        lemmatization, 0, change(lemmatization[0])
    )


def _change_manuscripts(
    change: Callable[
        [Sequence[Sequence[LemmatizationToken]]], Sequence[Sequence[LemmatizationToken]]
    ],
) -> LemmatizationChange:
    return _change_first_variant(
        lambda variant: attr.evolve(
            variant, manuscripts=tuple(change(variant.manuscripts))
        )
    )


def _change_reconstruction_token(
    token_index: int, change: TokenChange
) -> LemmatizationChange:
    return _change_first_variant(
        lambda variant: attr.evolve(
            variant,
            reconstruction=replace_item(
                variant.reconstruction,
                token_index,
                change(variant.reconstruction[token_index]),
            ),
        )
    )


def _change_manuscript_token(
    token_index: int, change: TokenChange
) -> LemmatizationChange:
    return _change_manuscripts(
        lambda manuscripts: replace_item(
            manuscripts,
            0,
            replace_item(
                manuscripts[0], token_index, change(manuscripts[0][token_index])
            ),
        )
    )


def _rename(value: str) -> TokenChange:
    return lambda token: attr.evolve(token, value=value)


def _lemmatize(token: LemmatizationToken) -> LemmatizationToken:
    return attr.evolve(token, unique_lemma=ANY_LEMMA)


LEMMATIZATION_CASES: Sequence[InvalidCase[LineLemmatizations]] = (
    InvalidCase(
        "no variants",
        lambda lemmatization: (),
        create_count_error("variants", 0, 1),
        re.escape("No lemmatization for line 0 variant 0 manuscript 0."),
    ),
    InvalidCase(
        "extra variant",
        lambda lemmatization: (*lemmatization, lemmatization[0]),
        create_count_error("variants", 2, 1),
        INVALID_LEMMATIZATION,
    ),
    InvalidCase(
        "missing variant without manuscripts",
        lambda lemmatization: lemmatization[:1],
        create_count_error("variants", 1, 2),
        INVALID_LEMMATIZATION,
        SPECIAL_INDEX,
    ),
    InvalidCase(
        "missing manuscript",
        _change_manuscripts(lambda manuscripts: manuscripts[:1]),
        create_count_error("manuscripts in variant 0", 1, 2),
        re.escape("No lemmatization for line 0 variant 0 manuscript 1."),
    ),
    InvalidCase(
        "extra manuscript",
        _change_manuscripts(lambda manuscripts: (*manuscripts, manuscripts[0])),
        create_count_error("manuscripts in variant 0", 3, 2),
        INVALID_LEMMATIZATION,
    ),
    InvalidCase(
        "missing manuscript token",
        _change_manuscripts(
            lambda manuscripts: replace_item(manuscripts, 1, manuscripts[1][:1])
        ),
        create_count_error("tokens in variant 0 manuscript 1", 1, 2),
        INVALID_LEMMATIZATION,
    ),
    InvalidCase(
        "token of an empty manuscript line",
        _change_manuscripts(
            lambda manuscripts: replace_item(
                manuscripts, 1, (LemmatizationToken("ku"),)
            )
        ),
        create_count_error("tokens in variant 0 manuscript 1", 1, 0),
        None,
        SPECIAL_INDEX,
    ),
    InvalidCase(
        "missing reconstruction token",
        _change_first_variant(
            lambda variant: attr.evolve(
                variant, reconstruction=variant.reconstruction[:3]
            )
        ),
        create_count_error("reconstruction tokens in variant 0", 3, 4),
        INVALID_LEMMATIZATION,
    ),
    InvalidCase(
        "other reconstruction value",
        _change_reconstruction_token(1, _rename("eliš")),
        INCOMPATIBLE_WORD_LEMMA,
        INCOMPATIBLE_WORD_LEMMA,
    ),
    InvalidCase(
        "lemma on a reconstruction token that is not a word",
        _change_reconstruction_token(2, _lemmatize),
        INCOMPATIBLE_TOKEN_LEMMA,
        INCOMPATIBLE_TOKEN_LEMMA,
    ),
    InvalidCase(
        "lemma on a reconstruction word that is not lemmatizable",
        _change_reconstruction_token(3, _lemmatize),
        INCOMPATIBLE_WORD_LEMMA,
        INCOMPATIBLE_WORD_LEMMA,
        SPECIAL_INDEX,
    ),
    InvalidCase(
        "other manuscript value",
        _change_manuscript_token(0, _rename("nu")),
        INCOMPATIBLE_WORD_LEMMA,
        INCOMPATIBLE_WORD_LEMMA,
    ),
    InvalidCase(
        "lemma on a manuscript word that is not lemmatizable",
        _change_manuscript_token(1, _lemmatize),
        INCOMPATIBLE_WORD_LEMMA,
        INCOMPATIBLE_WORD_LEMMA,
        SPECIAL_INDEX,
    ),
    InvalidCase(
        "lemma on a manuscript token that is not a word",
        _change_manuscript_token(2, _lemmatize),
        INCOMPATIBLE_TOKEN_LEMMA,
        INCOMPATIBLE_TOKEN_LEMMA,
        SPECIAL_INDEX,
    ),
)
INVALID_LEMMATIZATIONS: Sequence[InvalidAnnotation] = tuple(
    map(LEMMATIZATION.create_invalid, LEMMATIZATION_CASES)
)
