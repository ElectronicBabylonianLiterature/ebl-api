from typing import Sequence

import factory.fuzzy  # pyre-ignore
import pydash  # pyre-ignore

from ebl.corpus.domain.enums import (
    Classification,
    ManuscriptType,
    Period,
    PeriodModifier,
    Provenance,
    Stage,
)
from ebl.transliteration.domain.reconstructed_text import (
    AkkadianWord,
    Caesura,
    Lacuna,
    MetricalFootSeparator,
)
from ebl.corpus.domain.text import Chapter, Line, Manuscript, ManuscriptLine, Text
from ebl.tests.factories.bibliography import ReferenceWithDocumentFactory
from ebl.tests.factories.collections import TupleFactory
from ebl.transliteration.domain.atf import Flag, Status, Surface
from ebl.transliteration.domain.enclosure_tokens import BrokenAway
from ebl.transliteration.domain.labels import ColumnLabel, SurfaceLabel
from ebl.transliteration.domain.line_number import LineNumber
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

    id = factory.Sequence(lambda n: n)
    siglum_disambiguator = factory.Faker("word")
    museum_number = factory.Sequence(lambda n: f"M.{n}" if pydash.is_odd(n) else "")
    accession = factory.Sequence(lambda n: f"A.{n}" if pydash.is_even(n) else "")
    period_modifier = factory.fuzzy.FuzzyChoice(PeriodModifier)
    period = factory.fuzzy.FuzzyChoice(Period)
    provenance = factory.fuzzy.FuzzyChoice(Provenance)
    type = factory.fuzzy.FuzzyChoice(ManuscriptType)
    notes = factory.Faker("sentence")
    references = factory.List(
        [factory.SubFactory(ReferenceWithDocumentFactory)], TupleFactory
    )


class ManuscriptLineFactory(factory.Factory):  # pyre-ignore[11]
    class Meta:
        model = ManuscriptLine

    manuscript_id = factory.Sequence(lambda n: n)
    labels = (
        SurfaceLabel.from_label(Surface.OBVERSE),
        ColumnLabel.from_label("iii", [Status.COLLATION, Status.CORRECTION]),
    )
    line = TextLine.of_iterable(
        LineNumber(1),
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


class LineFactory(factory.Factory):  # pyre-ignore[11]
    class Meta:
        model = Line

    number = factory.Sequence(lambda n: LineNumber(n))
    reconstruction = (
        LanguageShift.normalized_akkadian(),
        AkkadianWord.of((ValueToken.of("buāru"),)),
        MetricalFootSeparator.uncertain(),
        Lacuna.of((BrokenAway.open(),), tuple()),
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
    manuscripts: Sequence[ManuscriptLine] = factory.List(
        [factory.SubFactory(ManuscriptLineFactory)], TupleFactory
    )


class ChapterFactory(factory.Factory):  # pyre-ignore[11]
    class Meta:
        model = Chapter

    classification = factory.fuzzy.FuzzyChoice(Classification)
    stage = factory.fuzzy.FuzzyChoice(Stage)
    version = factory.Faker("word")
    name = factory.Faker("sentence")
    order = factory.Faker("pyint")
    manuscripts = factory.List([factory.SubFactory(ManuscriptFactory)], TupleFactory)
    lines = factory.List([factory.SubFactory(LineFactory)], TupleFactory)
    parser_version = ""


class TextFactory(factory.Factory):  # pyre-ignore[11]
    class Meta:
        model = Text

    category = factory.Sequence(lambda n: n)
    index = factory.Sequence(lambda n: n)
    name = factory.Faker("sentence")
    number_of_verses = factory.fuzzy.FuzzyInteger(1, 10000)
    approximate_verses = factory.Iterator([True, False])
    chapters = factory.List([factory.SubFactory(ChapterFactory)], TupleFactory)
