from factory.base import Factory
from factory.declarations import List, SelfAttribute, Sequence, SubFactory, Trait
from factory.faker import Faker
from factory.fuzzy import FuzzyChoice

from ebl.corpus.domain.line import Line
from ebl.corpus.domain.line_variant import LineVariant
from ebl.corpus.domain.manuscript_line import ManuscriptLine
from ebl.tests.factories.bibliography import ReferenceFactory
from ebl.tests.factories.collections import TUPLE_FACTORY
from ebl.tests.factories.factory_meta import FactoryMeta
from ebl.tests.factories.parallel_line import (
    ParallelCompositionFactory,
    ParallelFragmentFactory,
    ParallelTextFactory,
)
from ebl.transliteration.domain.atf import Flag, Ruling, Status, Surface
from ebl.transliteration.domain.dollar_line import RulingDollarLine
from ebl.transliteration.domain.enclosure_tokens import BrokenAway
from ebl.transliteration.domain.labels import ColumnLabel, SurfaceLabel
from ebl.transliteration.domain.line_number import LineNumber, OldLineNumber
from ebl.transliteration.domain.markup import StringPart
from ebl.transliteration.domain.normalized_akkadian import (
    AkkadianWord,
    Caesura,
    MetricalFootSeparator,
)
from ebl.transliteration.domain.note_line import NoteLine
from ebl.transliteration.domain.sign_tokens import Reading
from ebl.transliteration.domain.text_line import TextLine
from ebl.transliteration.domain.tokens import (
    Joiner,
    LanguageShift,
    UnknownNumberOfSigns,
    ValueToken,
)
from ebl.transliteration.domain.translation_line import TranslationLine
from ebl.transliteration.domain.word_tokens import Word


class ManuscriptLineFactory(Factory):
    class Meta(FactoryMeta):
        model = ManuscriptLine

    manuscript_id = Sequence(lambda n: n)
    labels = (
        SurfaceLabel.from_label(Surface.OBVERSE),
        ColumnLabel.from_label("iii", [Status.COLLATION, Status.CORRECTION]),
    )
    line = Sequence(
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


class LineVariantFactory(Factory):
    class Meta(FactoryMeta):
        model = LineVariant

    class Params:
        manuscript_id = Sequence(lambda n: n)
        manuscript = SubFactory(
            ManuscriptLineFactory,
            manuscript_id=SelfAttribute("..manuscript_id"),
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
    note = FuzzyChoice([None, NoteLine((StringPart("a note"),))])
    manuscripts = List([SelfAttribute("..manuscript")], TUPLE_FACTORY)
    intertext = FuzzyChoice([(), (StringPart("bar"),)])
    parallel_lines = List(
        [
            SubFactory(ParallelCompositionFactory),
            SubFactory(ParallelTextFactory),
            SubFactory(ParallelFragmentFactory),
        ],
        TUPLE_FACTORY,
    )


class OldLineNumberFactory(Factory):
    class Meta(FactoryMeta):
        model = OldLineNumber

    number = Faker("word")
    reference = SubFactory(ReferenceFactory, with_document=True)


class LineFactory(Factory):
    class Meta(FactoryMeta):
        model = Line

    class Params:
        manuscript_id = Sequence(lambda n: n)
        variant = SubFactory(
            LineVariantFactory, manuscript_id=SelfAttribute("..manuscript_id")
        )
        with_old_line_numbers = Trait(
            old_line_numbers=List([SubFactory(OldLineNumberFactory)], TUPLE_FACTORY)
        )

    number = Sequence(LineNumber)
    variants = List([SelfAttribute("..variant")], TUPLE_FACTORY)
    is_second_line_of_parallelism = Faker("boolean")
    is_beginning_of_section = Faker("boolean")
    translation = (TranslationLine((StringPart("foo"),), "en", None),)
