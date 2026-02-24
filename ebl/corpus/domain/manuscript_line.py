from typing import Optional, Sequence, Tuple, Union, cast, Callable

import attr

from ebl.transliteration.domain.dollar_line import DollarLine
from ebl.transliteration.domain.label_validator import validate_labels
from ebl.transliteration.domain.labels import Label
from ebl.transliteration.domain.line import EmptyLine
from ebl.transliteration.domain.line_number import AbstractLineNumber
from ebl.transliteration.domain.note_line import NoteLine
from ebl.transliteration.domain.text_line import AlignmentMap, TextLine
from ebl.transliteration.domain.tokens import Token
from ebl.corpus.domain.manuscript import Manuscript
from ebl.transliteration.domain.atf import Atf


ManuscriptLineLabel = Tuple[int, Sequence[Label], AbstractLineNumber]


@attr.s(auto_attribs=True, frozen=True)
class ManuscriptLine:
    manuscript_id: int
    labels: Sequence[Label] = attr.ib(validator=validate_labels)
    line: Union[TextLine, EmptyLine]
    paratext: Sequence[Union[DollarLine, NoteLine]] = ()
    omitted_words: Sequence[int] = ()

    @property
    def label(self) -> Optional[ManuscriptLineLabel]:
        return (
            (self.manuscript_id, self.labels, self.line.line_number)
            if isinstance(self.line, TextLine)
            else None
        )

    @property
    def line_prefix_atf(self) -> Atf:
        return (
            Atf(
                " ".join(
                    label_element.to_value()
                    for label_element in self.labels
                    if hasattr(label_element, "to_value")
                )
            )
            if self.labels
            else Atf("")
        )

    @property
    def is_beginning_of_side(self) -> bool:
        return (
            self.line.line_number.is_beginning_of_side
            if isinstance(self.line, TextLine)
            else False
        )

    @property
    def is_end_of_side(self) -> bool:
        return any(
            line.is_end_of for line in self.paratext if isinstance(line, DollarLine)
        )

    @property
    def is_empty(self) -> bool:
        return isinstance(self.line, EmptyLine)

    def get_atf(self, get_manuscript: Callable[[int], Manuscript]) -> Atf:
        if self.is_empty:
            return Atf("")
        siglum = get_manuscript(self.manuscript_id).siglum
        line_prefix = f"{self.line_prefix_atf} " if self.line_prefix_atf else ""
        paratext = "\n".join([paratext.atf for paratext in self.paratext])
        paratext = f"\n{paratext}" if self.paratext else ""
        return Atf(f"{siglum} {line_prefix}{self.line.atf}{paratext}")

    def merge(self, other: "ManuscriptLine") -> "ManuscriptLine":
        merged_line = self.line.merge(other.line)
        return attr.evolve(other, line=merged_line)

    def update_alignments(self, alignment_map: AlignmentMap) -> "ManuscriptLine":
        return attr.evolve(
            self,
            line=self.line.update_alignments(alignment_map),
            omitted_words=tuple(
                alignment_map[index]
                for index in self.omitted_words
                if index < len(alignment_map) and alignment_map[index] is not None
            ),
        )

    def get_line_content(self) -> Sequence[Token]:
        return () if self.is_empty else cast(TextLine, self.line).content

    def has_lemma(self, lemma: str) -> bool:
        return any(
            lemma in getattr(token, "unique_lemma", [])
            for token in self.get_line_content()
        )
