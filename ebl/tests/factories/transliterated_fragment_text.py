from ebl.corpus.domain.chapter import Stage
from ebl.transliteration.domain.text_id import TextId

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
    Reading,
)
from ebl.transliteration.domain.text import Text
from ebl.transliteration.domain.text_line import TextLine
from ebl.transliteration.domain.tokens import (
    LanguageShift,
    ValueToken,
    Variant,
)
from ebl.transliteration.domain.word_tokens import Word
from ebl.tests.factories.transliterated_fragment_lines import FIRST_TEXT_LINES


TRANSLITERATED_FRAGMENT_TEXT = Text(
    FIRST_TEXT_LINES
    + (
        TextLine.of_iterable(
            LineNumber(7, True),
            (
                Word.of(
                    [Variant.of(Reading.of_name("šu"), CompoundGrapheme.of(["BI×IS"]))]
                ),
                LanguageShift.normalized_akkadian(),
                AkkadianWord.of([ValueToken.of("kur")]),
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
