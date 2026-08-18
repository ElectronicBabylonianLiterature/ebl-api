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
from ebl.transliteration.domain.atf import Flag
from ebl.transliteration.domain.dollar_line import (
    ImageDollarLine,
    LooseDollarLine,
    RulingDollarLine,
    ScopeContainer,
    SealDollarLine,
    StateDollarLine,
)
from ebl.transliteration.domain.enclosure_tokens import BrokenAway
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
    UnknownNumberOfSigns,
    ValueToken,
    Variant,
)
from ebl.transliteration.domain.unknown_sign_tokens import UnclearSign
from ebl.transliteration.domain.word_tokens import InWordNewline, Word


LEMMATIZED_FRAGMENT_TEXT = Text(
    (
        FIRST_TEXT_LINE,
        TextLine.of_iterable(
            LineNumber(2, True),
            (
                Word.of([BrokenAway.open(), UnknownNumberOfSigns.of()]),
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
                Word.of([UnknownNumberOfSigns.of(), BrokenAway.close()]),
            ),
        ),
        TextLine.of_iterable(
            LineNumber(3, True),
            (
                Word.of([BrokenAway.open(), UnknownNumberOfSigns.of()]),
                Word.of(
                    unique_lemma=(WordId("kīdu I"),),
                    parts=[
                        Reading.of(
                            (
                                ValueToken.of("k"),
                                BrokenAway.close(),
                                ValueToken.of("i"),
                            )
                        ),
                        Joiner.hyphen(),
                        Reading.of_name("du"),
                    ],
                ),
                Word.of(unique_lemma=(WordId("u I"),), parts=[Reading.of_name("u")]),
                Word.of(
                    unique_lemma=(WordId("bamātu I"),),
                    parts=[
                        Reading.of_name("ba"),
                        Joiner.hyphen(),
                        Reading.of_name("ma"),
                        Joiner.hyphen(),
                        Reading.of(
                            (
                                ValueToken.of("t"),
                                BrokenAway.open(),
                                ValueToken.of("i"),
                            )
                        ),
                    ],
                ),
                Word.of([UnknownNumberOfSigns.of(), BrokenAway.close()]),
            ),
        ),
        TextLine.of_iterable(
            LineNumber(6, True),
            (
                Word.of(
                    [
                        BrokenAway.open(),
                        UnknownNumberOfSigns.of(),
                        BrokenAway.close(),
                    ]
                ),
                Word.of([UnclearSign.of([Flag.DAMAGE])]),
                Word.of(unique_lemma=(WordId("mu I"),), parts=[Reading.of_name("mu")]),
                Word.of(
                    unique_lemma=(WordId("tamalāku I"),),
                    parts=[
                        Reading.of_name("ta"),
                        Joiner.hyphen(),
                        Reading.of_name("ma"),
                        InWordNewline.of(),
                        Joiner.hyphen(),
                        Reading.of_name("tu", 2),
                    ],
                ),
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
