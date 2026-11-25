import attr

from ebl.corpus.domain.chapter import Chapter
from ebl.dictionary.domain.word import WordId
from ebl.lemmatization.domain.lemmatization import LemmatizationToken
from ebl.transliteration.domain.enclosure_tokens import BrokenAway
from ebl.transliteration.domain.sign_tokens import Reading
from ebl.transliteration.domain.text_line import TextLine
from ebl.transliteration.domain.tokens import Joiner
from ebl.transliteration.domain.word_tokens import Word

LEMMA = (WordId("aklu I"),)


def lemmatize_first_line(chapter: Chapter) -> Chapter:
    line = chapter.lines[0]
    variant = line.variants[0]
    reconstruction = variant.reconstruction
    manuscript = variant.manuscripts[0]
    manuscript_line = manuscript.line
    assert isinstance(manuscript_line, TextLine)
    return attr.evolve(
        chapter,
        lines=(
            attr.evolve(
                line,
                variants=(
                    attr.evolve(
                        variant,
                        reconstruction=(
                            reconstruction[0],
                            reconstruction[1].set_unique_lemma(
                                LemmatizationToken(reconstruction[1].value, LEMMA)
                            ),
                            *reconstruction[2:6],
                            reconstruction[6].set_unique_lemma(
                                LemmatizationToken(reconstruction[6].value, ())
                            ),
                        ),
                        manuscripts=(
                            attr.evolve(
                                manuscript,
                                line=TextLine.of_iterable(
                                    manuscript_line.line_number,
                                    (
                                        Word.of(
                                            [
                                                Reading.of_name("ku"),
                                                Joiner.hyphen(),
                                                BrokenAway.open(),
                                                Reading.of_name("nu"),
                                                Joiner.hyphen(),
                                                Reading.of_name("ši"),
                                                BrokenAway.close(),
                                            ],
                                            unique_lemma=LEMMA,
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                ),
            ),
        ),
    )
