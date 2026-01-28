from functools import singledispatch
from typing import Iterator, Optional, Sequence, Set, Callable

import attr
import pydash

from ebl.corpus.domain.create_alignment_map import create_alignment_map
from ebl.corpus.domain.enclosure_validator import validate
from ebl.corpus.domain.manuscript_line import ManuscriptLine, ManuscriptLineLabel
from ebl.merger import Merger
from ebl.transliteration.domain.enclosure_visitor import set_enclosure_type
from ebl.transliteration.domain.language_visitor import set_language
from ebl.transliteration.domain.markup import MarkupPart
from ebl.transliteration.domain.note_line import NoteLine
from ebl.transliteration.domain.parallel_line import ParallelLine
from ebl.transliteration.domain.text_line import TextLine, merge_tokens
from ebl.transliteration.domain.tokens import Token
from ebl.transliteration.domain.word_tokens import AbstractWord
from ebl.corpus.domain.manuscript import Manuscript
from ebl.transliteration.domain.atf import Atf


@attr.s(auto_attribs=True, frozen=True)
class LineVariant:
    reconstruction: Sequence[Token] = attr.ib(
        converter=pydash.flow(set_enclosure_type, set_language)
    )
    note: Optional[NoteLine] = None
    manuscripts: Sequence[ManuscriptLine] = ()
    parallel_lines: Sequence[ParallelLine] = ()
    intertext: Sequence[MarkupPart] = ()

    @reconstruction.validator
    def validate_reconstruction(self, _, value):
        validate(value)

    @property
    def reconstruction_atf(self) -> Atf:
        return Atf(" ".join([token.value for token in self.reconstruction]))

    @property
    def note_atf(self) -> Atf:
        return self.note.atf if self.note else Atf("")

    @property
    def parallels_atf(self) -> Atf:
        return (
            Atf("\n".join(parallel.atf for parallel in self.parallel_lines))
            if self.parallel_lines
            else Atf("")
        )

    def get_manuscript_lines_atf(
        self, get_manuscript: Callable[[int], Manuscript]
    ) -> Atf:
        atf_lines = [
            manuscript_line.get_atf(get_manuscript)
            for manuscript_line in self.manuscripts
        ]
        return Atf("\n".join(atf_line for atf_line in atf_lines if atf_line))

    @property
    def manuscript_ids(self) -> Sequence[int]:
        return [manuscript.manuscript_id for manuscript in self.manuscripts]

    @property
    def manuscript_line_labels(self) -> Sequence[ManuscriptLineLabel]:
        return [
            manuscript_line.label
            for manuscript_line in self.manuscripts
            if manuscript_line.label
        ]

    @property
    def _variant_alignments(self) -> Set[Optional[int]]:
        return {
            manuscript_token.alignment
            for manuscript in self.manuscripts
            for manuscript_token in manuscript.get_line_content()
            if isinstance(manuscript_token, AbstractWord)
            if manuscript_token.has_variant
        }

    @property
    def _omitted_words(self) -> Set[Optional[int]]:
        return {
            index
            for manuscript in self.manuscripts
            for index in manuscript.omitted_words
        }

    def get_manuscript_line(self, manuscript_id: int) -> Optional[ManuscriptLine]:
        return (
            pydash.chain(self.manuscripts)
            .filter(lambda manuscript: manuscript.manuscript_id == manuscript_id)
            .head()
            .value()
        )

    def get_manuscript_text_lines(self, manuscript_id: int) -> Iterator[TextLine]:
        for manuscript in self.manuscripts:
            if manuscript.manuscript_id == manuscript_id and isinstance(
                manuscript.line, TextLine
            ):
                yield manuscript.line

    def get_manuscript_text_line(self, manuscript_id: int) -> Optional[TextLine]:
        return next(self.get_manuscript_text_lines(manuscript_id), None)

    def merge(self, other: "LineVariant") -> "LineVariant":
        merged_reconstruction = merge_tokens(self.reconstruction, other.reconstruction)
        alignment_map = create_alignment_map(self.reconstruction, merged_reconstruction)

        def merge_manuscript(
            old: ManuscriptLine, new: ManuscriptLine
        ) -> ManuscriptLine:
            return old.merge(new).update_alignments(alignment_map)

        merged_manuscripts = Merger(repr, merge_manuscript).merge(
            self.manuscripts, other.manuscripts
        )
        return attr.evolve(
            other,
            reconstruction=merged_reconstruction,
            manuscripts=tuple(merged_manuscripts),
        ).set_alignment_flags()

    def set_alignment_flags(self) -> "LineVariant":
        return self.set_has_variant_alignment().set_has_omitted_alignment()

    def set_has_variant_alignment(self) -> "LineVariant":
        @singledispatch
        def set_flag(token: Token, index: int) -> Token:
            return token

        @set_flag.register(AbstractWord)
        def _(token: AbstractWord, index: int) -> AbstractWord:
            return token.set_has_variant_alignment(index in self._variant_alignments)

        return attr.evolve(
            self,
            reconstruction=tuple(
                set_flag(token, index)
                for index, token in enumerate(self.reconstruction)
            ),
        )

    def set_has_omitted_alignment(self) -> "LineVariant":
        @singledispatch
        def set_flag(token: Token, index: int) -> Token:
            return token

        @set_flag.register(AbstractWord)
        def _(token: AbstractWord, index: int) -> AbstractWord:
            return token.set_has_omitted_alignment(index in self._omitted_words)

        return attr.evolve(
            self,
            reconstruction=tuple(
                set_flag(token, index)
                for index, token in enumerate(self.reconstruction)
            ),
        )
