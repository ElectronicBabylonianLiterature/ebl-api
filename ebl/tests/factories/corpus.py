from typing import Sequence

import factory.fuzzy  # pyre-ignore[21]
import pydash  # pyre-ignore[21]

from ebl.corpus.domain.chapter import (
    Chapter,
    Classification,
    Line,
    LineVariant,
    ManuscriptLine,
    Stage,
)
from ebl.corpus.domain.manuscript import (
    Manuscript,
    ManuscriptType,
    Period,
    PeriodModifier,
    Provenance,
)
from ebl.corpus.domain.text import Text
from ebl.fragmentarium.domain.museum_number import MuseumNumber
from ebl.tests.factories.bibliography import ReferenceFactory
from ebl.tests.factories.collections import TupleFactory
from ebl.transliteration.domain.atf import Flag, Ruling, Status, Surface
from ebl.transliteration.domain.dollar_line import RulingDollarLine
from ebl.transliteration.domain.enclosure_tokens import BrokenAway
from ebl.transliteration.domain.labels import ColumnLabel, SurfaceLabel
from ebl.transliteration.domain.line_number import LineNumber
from ebl.transliteration.domain.normalized_akkadian import (
    AkkadianWord,
    Caesura,
    MetricalFootSeparator,
)
from ebl.transliteration.domain.note_line import NoteLine, StringPart
from ebl.transliteration.domain.sign_tokens import Reading
from ebl.transliteration.domain.text_line import TextLine
from ebl.transliteration.domain.tokens import (
    Joiner,
    LanguageShift,
    UnknownNumberOfSigns,
    ValueToken,
)
from ebl.transliteration.domain.word_tokens import Word


class ManuscriptFactory(factory.Factory):  # pyre-ignore[11]
    class Meta:
        model = Manuscript

    id = factory.Sequence(lambda n: n + 1)
    siglum_disambiguator = factory.Faker("word")
    museum_number = factory.Sequence(
        lambda n: MuseumNumber("M", str(n)) if pydash.is_odd(n) else None
    )
    accession = factory.Sequence(lambda n: f"A.{n}" if pydash.is_even(n) else "")
    period_modifier = factory.fuzzy.FuzzyChoice(PeriodModifier)
    period = factory.fuzzy.FuzzyChoice(Period)
    provenance = factory.fuzzy.FuzzyChoice(Provenance)
    type = factory.fuzzy.FuzzyChoice(ManuscriptType)
    notes = factory.Faker("sentence")
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
    manuscripts: Sequence[ManuscriptLine] = factory.List(
        [factory.SelfAttribute("..manuscript")], TupleFactory
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
    variants: Sequence[LineVariant] = factory.List(
        [factory.SelfAttribute("..variant")], TupleFactory
    )
    is_second_line_of_parallelism = factory.Faker("boolean")
    is_beginning_of_section = factory.Faker("boolean")


class ChapterFactory(factory.Factory):
    class Meta:
        model = Chapter

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
    parser_version = ""


class TextFactory(factory.Factory):
    class Meta:
        model = Text

    category = factory.Sequence(lambda n: n)
    index = factory.Sequence(lambda n: n)
    name = factory.Faker("sentence")
    number_of_verses = factory.fuzzy.FuzzyInteger(1, 10000)
    approximate_verses = factory.Iterator([True, False])
    chapters = factory.List([factory.SubFactory(ChapterFactory)], TupleFactory)
