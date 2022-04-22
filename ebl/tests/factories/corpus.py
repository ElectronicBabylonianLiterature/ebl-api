import factory.fuzzy
import pydash

from ebl.corpus.domain.chapter import Chapter, Classification
from ebl.corpus.domain.line import Line, LineVariant, ManuscriptLine
from ebl.corpus.domain.manuscript import (
    Manuscript,
    ManuscriptType,
    OldSiglum,
    Period,
    PeriodModifier,
    Provenance,
)
from ebl.corpus.domain.record import Author, AuthorRole, Record, Translator
from ebl.corpus.domain.text import ChapterListing, Text
from ebl.tests.factories.bibliography import ReferenceFactory
from ebl.tests.factories.collections import TupleFactory
from ebl.tests.factories.ids import TextIdFactory
from ebl.tests.factories.parallel_line import (
    ParallelCompositionFactory,
    ParallelFragmentFactory,
    ParallelTextFactory,
)
from ebl.transliteration.domain.atf import Flag, Ruling, Status, Surface
from ebl.transliteration.domain.dollar_line import RulingDollarLine
from ebl.transliteration.domain.enclosure_tokens import BrokenAway
from ebl.transliteration.domain.genre import Genre
from ebl.transliteration.domain.labels import ColumnLabel, SurfaceLabel
from ebl.transliteration.domain.line_number import LineNumber
from ebl.transliteration.domain.markup import StringPart
from ebl.transliteration.domain.museum_number import MuseumNumber
from ebl.transliteration.domain.normalized_akkadian import (
    AkkadianWord,
    Caesura,
    MetricalFootSeparator,
)
from ebl.transliteration.domain.note_line import NoteLine
from ebl.transliteration.domain.sign_tokens import Reading
from ebl.transliteration.domain.stage import Stage
from ebl.transliteration.domain.text import Text as Transliteration
from ebl.transliteration.domain.text_line import TextLine
from ebl.transliteration.domain.tokens import (
    Joiner,
    LanguageShift,
    UnknownNumberOfSigns,
    ValueToken,
)
from ebl.transliteration.domain.translation_line import TranslationLine
from ebl.transliteration.domain.word_tokens import Word


class OldSiglumFactory(factory.Factory):
    class Meta:
        model = OldSiglum

    siglum = factory.Faker("word")
    reference = factory.SubFactory(ReferenceFactory)


class ManuscriptFactory(factory.Factory):
    class Meta:
        model = Manuscript

    id = factory.Sequence(lambda n: n + 1)
    siglum_disambiguator = factory.Faker("word")
    old_sigla = factory.List([factory.SubFactory(OldSiglumFactory)], TupleFactory)
    museum_number = factory.Sequence(
        lambda n: MuseumNumber("M", str(n)) if pydash.is_odd(n) else None
    )
    accession = factory.Sequence(lambda n: f"A.{n}" if pydash.is_even(n) else "")
    period_modifier = factory.fuzzy.FuzzyChoice(PeriodModifier)
    period = factory.fuzzy.FuzzyChoice(set(Period) - {Period.NONE})
    provenance = factory.fuzzy.FuzzyChoice(set(Provenance) - {Provenance.STANDARD_TEXT})
    type = factory.fuzzy.FuzzyChoice(set(ManuscriptType) - {ManuscriptType.NONE})
    notes = factory.Faker("sentence")
    colophon = Transliteration.of_iterable(
        [TextLine.of_iterable(LineNumber(1, True), (Word.of([Reading.of_name("ku")]),))]
    )
    unplaced_lines = Transliteration.of_iterable(
        [TextLine.of_iterable(LineNumber(1, True), (Word.of([Reading.of_name("nu")]),))]
    )
    references = factory.List(
        [factory.SubFactory(ReferenceFactory, with_document=True)], TupleFactory
    )


class ManuscriptLineFactory(factory.Factory):
    class Meta:
        model = ManuscriptLine

    manuscript_id = factory.Sequence(lambda n: n)
    labels = (
        SurfaceLabel.from_label(Surface.OBVERSE),
        ColumnLabel.from_label("iii", [Status.COLLATION, Status.CORRECTION]),
    )
    line = factory.Sequence(
        lambda n: TextLine.of_iterable(
            LineNumber(n),
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
                    ]
                ),
            ),
        )
    )
    paratext = (NoteLine((StringPart("note"),)), RulingDollarLine(Ruling.SINGLE))
    omitted_words = (1,)


class LineVariantFactory(factory.Factory):
    class Meta:
        model = LineVariant

    class Params:
        manuscript_id = factory.Sequence(lambda n: n)
        manuscript = factory.SubFactory(
            ManuscriptLineFactory,
            manuscript_id=factory.SelfAttribute("..manuscript_id"),
        )

    reconstruction = (
        LanguageShift.normalized_akkadian(),
        AkkadianWord.of((ValueToken.of("buāru"),)),
        MetricalFootSeparator.uncertain(),
        BrokenAway.open(),
        UnknownNumberOfSigns.of(),
        Caesura.certain(),
        AkkadianWord.of(
            (
                UnknownNumberOfSigns.of(),
                BrokenAway.close(),
                Joiner.hyphen(),
                ValueToken.of("buāru"),
            ),
            (Flag.DAMAGE,),
        ),
    )
    note = factory.fuzzy.FuzzyChoice([None, NoteLine((StringPart("a note"),))])
    manuscripts = factory.List([factory.SelfAttribute("..manuscript")], TupleFactory)
    intertext = factory.fuzzy.FuzzyChoice([tuple(), (StringPart("bar"),)])
    parallel_lines = factory.List(
        [
            factory.SubFactory(ParallelCompositionFactory),
            factory.SubFactory(ParallelTextFactory),
            factory.SubFactory(ParallelFragmentFactory),
        ],
        TupleFactory,
    )


class LineFactory(factory.Factory):
    class Meta:
        model = Line

    class Params:
        manuscript_id = factory.Sequence(lambda n: n)
        variant = factory.SubFactory(
            LineVariantFactory, manuscript_id=factory.SelfAttribute("..manuscript_id")
        )

    number = factory.Sequence(lambda n: LineNumber(n))
    variants = factory.List([factory.SelfAttribute("..variant")], TupleFactory)
    is_second_line_of_parallelism = factory.Faker("boolean")
    is_beginning_of_section = factory.Faker("boolean")
    translation = (TranslationLine((StringPart("foo"),), "en", None),)


class AuthorFactory(factory.Factory):
    class Meta:
        model = Author

    name = factory.Faker("word")
    prefix = factory.Faker("word")
    role = factory.fuzzy.FuzzyChoice(AuthorRole)
    orcid_number = ""


class TranslatorFactory(factory.Factory):
    class Meta:
        model = Translator

    name = factory.Faker("word")
    prefix = factory.Faker("word")
    orcid_number = ""
    language = factory.fuzzy.FuzzyChoice(["en", "ar", "de"])


class RecordFactory(factory.Factory):
    class Meta:
        model = Record

    authors = factory.List([factory.SubFactory(AuthorFactory)], TupleFactory)
    translators = factory.List([factory.SubFactory(TranslatorFactory)], TupleFactory)
    publication_date = "2020-05-11T07:46:47.743916"


class ChapterFactory(factory.Factory):
    class Meta:
        model = Chapter

    text_id = factory.SubFactory(TextIdFactory)
    classification = factory.fuzzy.FuzzyChoice(Classification)
    stage = factory.fuzzy.FuzzyChoice(Stage)
    version = factory.Faker("word")
    name = factory.Faker("sentence")
    order = factory.Faker("pyint")
    manuscripts = factory.List(
        [factory.SubFactory(ManuscriptFactory, id=1)], TupleFactory
    )
    lines = factory.List(
        [factory.SubFactory(LineFactory, manuscript_id=1)], TupleFactory
    )
    signs = ("KU ABZ075 ABZ207a\\u002F207b\\u0020X\nKU\nABZ075",)
    record = factory.SubFactory(RecordFactory)
    parser_version = ""


class ChapterListingFactory(factory.Factory):
    class Meta:
        model = ChapterListing

    stage = factory.fuzzy.FuzzyChoice(Stage)
    name = factory.Faker("sentence")
    translation = (TranslationLine((StringPart("foo"),), "en", None),)
    uncertain_fragments = tuple()


class TextFactory(factory.Factory):
    class Meta:
        model = Text

    genre = factory.fuzzy.FuzzyChoice(Genre)
    category = factory.Sequence(lambda n: n)
    index = factory.Sequence(lambda n: n)
    name = factory.Faker("sentence")
    has_doi = factory.Iterator([True, False])
    number_of_verses = factory.fuzzy.FuzzyInteger(1, 10000)
    approximate_verses = factory.Iterator([True, False])
    intro = factory.Faker("sentence")
    chapters = factory.List([factory.SubFactory(ChapterListingFactory)], TupleFactory)
    references = factory.List(
        [factory.SubFactory(ReferenceFactory, with_document=True)], TupleFactory
    )
