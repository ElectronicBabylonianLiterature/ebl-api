from typing import Sequence

import attr

from ebl.corpus.domain.chapter import Chapter
from ebl.corpus.domain.line import Line
from ebl.corpus.domain.manuscript import Manuscript
from ebl.tests.corpus.line_move_support import MANUSCRIPT_IDS
from ebl.tests.factories.corpus import (
    LineFactory,
)
from ebl.tests.factories.corpus_lines import LineVariantFactory, ManuscriptLineFactory
from ebl.transliteration.domain import atf
from ebl.transliteration.domain.dollar_line import RulingDollarLine
from ebl.transliteration.domain.line import EmptyLine
from ebl.transliteration.domain.line_number import LineNumber
from ebl.transliteration.domain.markup import EmphasisPart, StringPart
from ebl.transliteration.domain.museum_number import MuseumNumber
from ebl.transliteration.domain.normalized_akkadian import AkkadianWord
from ebl.transliteration.domain.note_line import NoteLine
from ebl.transliteration.domain.sign_tokens import Reading
from ebl.transliteration.domain.text_line import TextLine
from ebl.transliteration.domain.tokens import LanguageShift, ValueToken
from ebl.transliteration.domain.translation_line import TranslationLine
from ebl.transliteration.domain.word_tokens import Word

DOLLAR_SIGNS: Sequence[str] = ("$name", "$$ROOT")
DOLLAR_VERSION = "$parserVersion"
DOLLAR_NOTES = "$textId.genre"
DOLLAR_FRAGMENTS: Sequence[MuseumNumber] = (MuseumNumber("$K", "$1"),)
DOLLAR_TRANSLATION = "$lines"
DOLLAR_NOTE = "$$REMOVE"
DOLLAR_PARATEXT = "$stage"
DOLLAR_TEXT = "$signs"
DOLLAR_RECONSTRUCTION = "$order"
DOLLAR_PREFIX = "$"
SERVER_KEYS = {
    "$slice": ["$lines", 0, 1],
    "a.b": "$name",
    "$literal": {"$set": [], "x.y": {}},
    "empty": [],
}


def create_dollar_line(number: int) -> Line:
    text_id, empty_id = MANUSCRIPT_IDS
    return LineFactory.build(
        number=LineNumber(number),
        translation=(TranslationLine((StringPart(DOLLAR_TRANSLATION),), "en", None),),
        variants=(
            LineVariantFactory.build(
                reconstruction=(
                    LanguageShift.normalized_akkadian(),
                    AkkadianWord.of((ValueToken.of(DOLLAR_RECONSTRUCTION),)),
                ),
                note=NoteLine((StringPart(DOLLAR_NOTE), EmphasisPart("$version"))),
                manuscripts=(
                    ManuscriptLineFactory.build(
                        manuscript_id=text_id,
                        labels=(),
                        line=TextLine.of_iterable(
                            LineNumber(number),
                            (
                                Word.of([Reading.of_name("ku")]),
                                ValueToken.of(DOLLAR_TEXT),
                            ),
                        ),
                        paratext=(
                            RulingDollarLine(atf.Ruling.SINGLE),
                            NoteLine((StringPart(DOLLAR_PARATEXT),)),
                        ),
                        omitted_words=(),
                    ),
                    ManuscriptLineFactory.build(
                        manuscript_id=empty_id,
                        labels=(),
                        line=EmptyLine(),
                        paratext=(),
                        omitted_words=(),
                    ),
                ),
                parallel_lines=(),
                intertext=(StringPart("$uncertainFragments"),),
            ),
            LineVariantFactory.build(
                reconstruction=(LanguageShift.normalized_akkadian(),),
                note=None,
                manuscripts=(),
                parallel_lines=(),
            ),
        ),
    )


def _add_dollar_notes(manuscript: Manuscript) -> Manuscript:
    return attr.evolve(manuscript, notes=DOLLAR_NOTES)


def add_dollar_fields(chapter: Chapter) -> Chapter:
    return attr.evolve(
        chapter,
        manuscripts=tuple(map(_add_dollar_notes, chapter.manuscripts)),
        uncertain_fragments=DOLLAR_FRAGMENTS,
        signs=DOLLAR_SIGNS,
        parser_version=DOLLAR_VERSION,
    )
