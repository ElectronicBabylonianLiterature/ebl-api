from collections import Counter
from typing import Union

from ebl.corpus.alignment import AlignmentError
from ebl.corpus.text import Chapter, Line, Manuscript, ManuscriptLine, \
    TextVisitor
from ebl.errors import DataError
from ebl.fragment.transliteration import Transliteration, TransliterationError
from ebl.fragmentarium.validator import Validator
from ebl.text.labels import LineNumberLabel
from ebl.text.token import BrokenAway, DocumentOrientedGloss, Erasure, \
    LanguageShift, OmissionOrRemoval, PerhapsBrokenAway, Token, TokenVisitor, \
    Word


def invalid_atf(chapter: Chapter,
                line_number: LineNumberLabel,
                manuscript_id: int) -> Exception:
    siglum = [manuscript.siglum
              for manuscript in chapter.manuscripts
              if manuscript.id == manuscript_id][0]
    return DataError(
        f'Invalid transliteration on'
        f' line {line_number.to_value()}'
        f' manuscript {siglum}.'
    )


class AlignmentVisitor(TokenVisitor):

    def __init__(self):
        self.alignments = []

    def visit_token(self, token: Token) -> None:
        pass

    def visit_language_shift(self, shift: LanguageShift) -> None:
        pass

    def visit_word(self, word: Word) -> None:
        if word.alignment is not None:
            self.alignments.append(word.alignment)

    def visit_document_oriented_gloss(self,
                                      gloss: DocumentOrientedGloss) -> None:
        pass

    def visit_broken_away(
            self, broken_away: Union[BrokenAway, PerhapsBrokenAway]
    ) -> None:
        pass

    def visit_omission_or_removal(
            self, omission: OmissionOrRemoval
    ) -> None:
        pass

    def visit_erasure(self, erasure: Erasure):
        pass

    def validate(self):
        if any(count > 1 for _, count in Counter(self.alignments).items()):
            raise AlignmentError()


class TextValidator(TextVisitor):

    def __init__(self, bibliography, sign_list):
        super().__init__(TextVisitor.Order.PRE)
        self._bibliography = bibliography
        self._sign_list = sign_list
        self._chapter = None
        self._line = None

    def visit_chapter(self, chapter: Chapter) -> None:
        self._chapter = chapter

    def visit_manuscript(self, manuscript: Manuscript) -> None:
        self._bibliography.validate_references(manuscript.references)

    def visit_line(self, line: Line) -> None:
        self._line = line

    def visit_manuscript_line(self, manuscript_line: ManuscriptLine) -> None:
        try:
            Validator(Transliteration(manuscript_line.line.atf)
                      .with_signs(self._sign_list)).validate()
        except TransliterationError:
            raise invalid_atf(self._chapter,
                              self._line.number,
                              manuscript_line.manuscript_id)

        alignment_validator = AlignmentVisitor()
        for token in manuscript_line.line.content:
            token.accept(alignment_validator)
        alignment_validator.validate()
