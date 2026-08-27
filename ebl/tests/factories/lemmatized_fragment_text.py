from ebl.corpus.domain.chapter import Stage
from ebl.transliteration.domain.text_id import TextId
from ebl.dictionary.domain.word import WordId

from ebl.transliteration.domain.museum_number import MuseumNumber
from ebl.transliteration.domain import atf
from ebl.transliteration.domain.at_line import (
    ColumnAtLine,
    CompositeAtLine,
    DiscourseAtLine,
    DivisionAtLine,
    HeadingAtLine,
    ObjectAtLine,
    SealAtLine,
    SurfaceAtLine,
)
from ebl.tests.factories.first_text_line import FIRST_TEXT_LINE
from ebl.tests.factories.fragment_text_words import (
    ba_ma_ti,
    broken_away_gap,
    broken_away_gap_end,
    broken_away_gap_start,
    damaged_unclear_sign,
    ki_du,
    mu,
    ta_ma_tu,
    u,
)
from ebl.transliteration.domain.dollar_line import (
    ImageDollarLine,
    LooseDollarLine,
    RulingDollarLine,
    ScopeContainer,
    SealDollarLine,
    StateDollarLine,
)
from ebl.transliteration.domain.genre import Genre as CorpusGenre
from ebl.transliteration.domain.labels import ColumnLabel, ObjectLabel, SurfaceLabel
from ebl.transliteration.domain.language import Language
from ebl.transliteration.domain.line_number import LineNumber
from ebl.transliteration.domain.markup import EmphasisPart, LanguagePart, StringPart
from ebl.transliteration.domain.normalized_akkadian import AkkadianWord
from ebl.transliteration.domain.note_line import NoteLine
from ebl.transliteration.domain.parallel_line import (
    ChapterName,
    Labels,
    ParallelComposition,
    ParallelFragment,
    ParallelText,
)
from ebl.transliteration.domain.sign_tokens import (
    CompoundGrapheme,
    Logogram,
    Reading,
)
from ebl.transliteration.domain.text import Text
from ebl.transliteration.domain.text_line import TextLine
from ebl.transliteration.domain.tokens import (
    Joiner,
    LanguageShift,
    ValueToken,
    Variant,
)
from ebl.transliteration.domain.word_tokens import Word


LEMMATIZED_FRAGMENT_TEXT = Text(
    (
        FIRST_TEXT_LINE,
        TextLine.of_iterable(
            LineNumber(2, True),
            (
                Word.of(broken_away_gap_start()),
                Word.of([Logogram.of_name("GI", 6)], unique_lemma=(WordId("ginâ I"),)),
                Word.of([Reading.of_name("ana")], unique_lemma=(WordId("ana I"),)),
                Word.of(
                    [
                        Reading.of_name("u₄"),
                        Joiner.hyphen(),
                        Reading.of_name("š[u"),
                    ],
                    unique_lemma=(WordId("ūsu I"),),
                ),
                Word.of(broken_away_gap_end()),
            ),
        ),
        TextLine.of_iterable(
            LineNumber(3, True),
            (
                Word.of(broken_away_gap_start()),
                Word.of(ki_du(), unique_lemma=(WordId("kīdu I"),)),
                Word.of(u(), unique_lemma=(WordId("u I"),)),
                Word.of(ba_ma_ti(), unique_lemma=(WordId("bamātu I"),)),
                Word.of(broken_away_gap_end()),
            ),
        ),
        TextLine.of_iterable(
            LineNumber(6, True),
            (
                Word.of(broken_away_gap()),
                Word.of(damaged_unclear_sign()),
                Word.of(mu(), unique_lemma=(WordId("mu I"),)),
                Word.of(ta_ma_tu(), unique_lemma=(WordId("tamalāku I"),)),
            ),
        ),
        TextLine.of_iterable(
            LineNumber(7, True),
            (
                Word.of(
                    [Variant.of(Reading.of_name("šu"), CompoundGrapheme.of(["BI×IS"]))]
                ),
                LanguageShift.normalized_akkadian(),
                AkkadianWord.of(
                    [ValueToken.of("kur")], unique_lemma=(WordId("normalized I"),)
                ),
            ),
        ),
        StateDollarLine(
            atf.Qualification.AT_LEAST,
            1,
            ScopeContainer(atf.Surface.OBVERSE, ""),
            atf.State.MISSING,
            None,
        ),
        ImageDollarLine("1", None, "numbered diagram of triangle"),
        RulingDollarLine(atf.Ruling.SINGLE),
        LooseDollarLine("this is a loose line"),
        SealDollarLine(1),
        SealAtLine(1),
        HeadingAtLine(1),
        ColumnAtLine(ColumnLabel([atf.Status.COLLATION], 1)),
        SurfaceAtLine(
            SurfaceLabel([atf.Status.COLLATION], atf.Surface.SURFACE, "stone wig")
        ),
        ObjectAtLine(
            ObjectLabel([atf.Status.COLLATION], atf.Object.OBJECT, "stone wig")
        ),
        DiscourseAtLine(atf.Discourse.DATE),
        DivisionAtLine("paragraph", 5),
        CompositeAtLine(atf.Composite.DIV, "part", 1),
        NoteLine(
            (
                StringPart("a note "),
                EmphasisPart("italic"),
                LanguagePart.of_transliteration(
                    Language.AKKADIAN, (Word.of([Reading.of_name("bu")]),)
                ),
            )
        ),
        ParallelComposition(False, "my name", LineNumber(1)),
        ParallelText(
            True,
            TextId(CorpusGenre.LITERATURE, 1, 1),
            ChapterName(Stage.OLD_BABYLONIAN, "", "my name"),
            LineNumber(1),
            False,
        ),
        ParallelFragment(
            False, MuseumNumber.of("K.1"), True, Labels(), LineNumber(1), False
        ),
    )
)
