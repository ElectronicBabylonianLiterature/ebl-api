from random import Random
from typing import Callable, List, Optional, Tuple

from ebl.corpus.application.chapter_edit_writer import ChapterEditWriter, SavedChapter
from ebl.corpus.application.lemmatization import LineLemmatization
from ebl.corpus.domain.alignment import LineAlignment
from ebl.corpus.domain.chapter import Chapter, ChapterId
from ebl.corpus.domain.line_move import LineMove
from ebl.corpus.domain.word_instances import WordLemma
from ebl.dictionary.domain.word import WordId
from ebl.errors import DataError
from ebl.lemmatization.domain.lemmatization import LemmatizationError
from ebl.tests.corpus.chapter_change_cases import create_random_lines_update
from ebl.tests.corpus.chapter_edit_support import (
    FIRST_IMPORTED_LINE_NUMBER,
    create_manuscripts_update,
)
from ebl.tests.corpus.line_annotation_support import (
    create_new_alignment,
    create_new_lemmatization,
)
from ebl.tests.corpus.support import ANY_USER
from ebl.tests.corpus.word_instances_support import MOVE_CHAPTER_WORD
from ebl.transliteration.domain.alignment import AlignmentError

Save = Callable[[ChapterEditWriter, ChapterId, str], SavedChapter]
SaveFactory = Callable[[Random, Chapter, int], Save]
SaveOutcome = Tuple[Optional[SavedChapter], str]
NUMBERS_PER_STEP = 1000
REFUSALS = (DataError, AlignmentError, LemmatizationError)


def _create_lines_save(random: Random, chapter: Chapter, step: int) -> Save:
    update = create_random_lines_update(chapter, random, NUMBERS_PER_STEP * (step + 1))
    return lambda writer, id_, revision: writer.save_lines(
        id_, update, revision, ANY_USER
    )


def _create_import_save(_: Random, chapter: Chapter, step: int) -> Save:
    atf = (
        f"{FIRST_IMPORTED_LINE_NUMBER + step}. bu\n"
        f"{chapter.manuscripts[0].siglum} {step + 1}. ku"
    )
    return lambda writer, id_, revision: writer.save_imported_lines(
        id_, atf, revision, ANY_USER
    )


def _create_manuscripts_save(_: Random, chapter: Chapter, step: int) -> Save:
    update = create_manuscripts_update(chapter, step)
    return lambda writer, id_, revision: writer.save_manuscripts(
        id_, update, revision, ANY_USER
    )


def _create_word_lemma_save(_: Random, __: Chapter, step: int) -> Save:
    word_lemma = WordLemma(MOVE_CHAPTER_WORD, (WordId(f"lemma{step} I"),))
    return lambda writer, id_, revision: writer.save_word_lemma(
        id_, word_lemma, revision, ANY_USER
    )


def _create_move_save(random: Random, chapter: Chapter, _: int) -> Save:
    source, target = random.sample(range(len(chapter.lines)), 2)
    return lambda writer, id_, revision: writer.move_line(
        id_, LineMove(source, target), revision, ANY_USER
    )


def _create_alignment_save(random: Random, chapter: Chapter, _: int) -> Save:
    index = random.randrange(len(chapter.lines))
    alignment = LineAlignment(index, create_new_alignment(chapter.lines[index]))
    return lambda writer, id_, revision: writer.save_line_alignment(
        id_, alignment, revision, ANY_USER
    )


def _create_lemmatization_save(random: Random, chapter: Chapter, _: int) -> Save:
    index = random.randrange(len(chapter.lines))
    lemmatization = LineLemmatization(
        index, create_new_lemmatization(chapter.lines[index])
    )
    return lambda writer, id_, revision: writer.save_line_lemmatization(
        id_, lemmatization, revision, ANY_USER
    )


CHAPTER_SAVES: List[SaveFactory] = [
    _create_lines_save,
    _create_import_save,
    _create_manuscripts_save,
    _create_word_lemma_save,
]
LINE_SAVES: List[SaveFactory] = [
    _create_alignment_save,
    _create_alignment_save,
    _create_lemmatization_save,
    _create_lemmatization_save,
]
MOVE_SAVES: List[SaveFactory] = [_create_move_save]


def create_random_save(random: Random, chapter: Chapter, step: int) -> Save:
    line_count = len(chapter.lines)
    factories = [
        *CHAPTER_SAVES,
        *(LINE_SAVES if line_count else []),
        *(MOVE_SAVES if line_count > 1 else []),
    ]
    return random.choice(factories)(random, chapter, step)


def try_save(
    save: Save, writer: ChapterEditWriter, id_: ChapterId, revision: str
) -> SaveOutcome:
    try:
        return save(writer, id_, revision), ""
    except REFUSALS as error:
        return None, f"{type(error).__name__}: {error}"
