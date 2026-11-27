from typing import Any, Dict, List, Sequence

from ebl.corpus.application.alignment_updater import (
    AlignmentUpdater,
    LineAlignmentUpdater,
)
from ebl.corpus.application.lemmatization import LineLemmatization
from ebl.corpus.application.lemmatization_updater import (
    LemmatizationUpdater,
    LineLemmatizationUpdater,
)
from ebl.corpus.domain.alignment import Alignment, LineAlignment
from ebl.corpus.domain.chapter_revision import LEGACY_REVISION
from ebl.lemmatization.domain.lemmatization import LemmatizationToken
from ebl.tests.corpus.line_annotation_kind import AnnotationKind
from ebl.tests.corpus.line_annotation_support import (
    LineAlignments,
    LineLemmatizations,
    create_new_alignment,
    create_new_lemmatization,
    find_line_alignment,
    find_line_lemmatization,
)
from ebl.tests.corpus.support import ANY_USER
from ebl.transliteration.domain.alignment import AlignmentToken


def _dump_alignment_token(token: AlignmentToken) -> Dict[str, Any]:
    variant = token.variant
    return {
        "value": token.value,
        **({} if token.alignment is None else {"alignment": token.alignment}),
        **(
            {}
            if variant is None
            else {
                "variant": variant.value,
                "type": type(variant).__name__,
                "language": variant.language.name,
            }
        ),
    }


def dump_alignment(alignment: LineAlignments) -> List[List[Dict[str, Any]]]:
    return [
        [
            {
                "alignment": list(map(_dump_alignment_token, manuscript.alignment)),
                "omittedWords": list(manuscript.omitted_words),
            }
            for manuscript in variant
        ]
        for variant in alignment
    ]


def _dump_lemmatization_tokens(
    tokens: Sequence[LemmatizationToken],
) -> List[Dict[str, Any]]:
    return [
        {
            "value": token.value,
            **(
                {}
                if token.unique_lemma is None
                else {"uniqueLemma": list(token.unique_lemma)}
            ),
        }
        for token in tokens
    ]


def dump_lemmatization(lemmatization: LineLemmatizations) -> List[Dict[str, Any]]:
    return [
        {
            "reconstruction": _dump_lemmatization_tokens(variant.reconstruction),
            "manuscripts": list(map(_dump_lemmatization_tokens, variant.manuscripts)),
        }
        for variant in lemmatization
    ]


ALIGNMENT: AnnotationKind[LineAlignments] = AnnotationKind(
    "alignment",
    find_line_alignment,
    create_new_alignment,
    dump_alignment,
    lambda index, alignment: LineAlignmentUpdater(LineAlignment(index, alignment)),
    lambda alignments: AlignmentUpdater(Alignment(tuple(alignments))),
    lambda writer, id_, index, alignment: writer.save_line_alignment(
        id_, LineAlignment(index, alignment), LEGACY_REVISION, ANY_USER
    ),
    lambda corpus, id_, alignments: corpus.update_alignment(
        id_, Alignment(tuple(alignments)), ANY_USER
    ),
)
LEMMATIZATION: AnnotationKind[LineLemmatizations] = AnnotationKind(
    "lemmatization",
    find_line_lemmatization,
    create_new_lemmatization,
    dump_lemmatization,
    lambda index, lemmatization: LineLemmatizationUpdater(
        LineLemmatization(index, lemmatization)
    ),
    LemmatizationUpdater,
    lambda writer, id_, index, lemmatization: writer.save_line_lemmatization(
        id_, LineLemmatization(index, lemmatization), LEGACY_REVISION, ANY_USER
    ),
    lambda corpus, id_, lemmatizations: corpus.update_manuscript_lemmatization(
        id_, lemmatizations, ANY_USER
    ),
)
ANNOTATION_KINDS: Sequence[AnnotationKind] = (ALIGNMENT, LEMMATIZATION)
