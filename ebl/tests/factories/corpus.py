from typing import Tuple

import factory.fuzzy
import pydash

from ebl.corpus.enums import Classification, ManuscriptType, Period, \
    PeriodModifier, Provenance, Stage
from ebl.corpus.text import (Chapter, Line, Manuscript, ManuscriptLine, Text)
from ebl.tests.factories.bibliography import ReferenceWithDocumentFactory
from ebl.tests.factories.collections import TupleFactory
from ebl.text.atf import Status, Surface
from ebl.text.enclosure import Enclosure, EnclosureType, EnclosureVariant
from ebl.text.labels import ColumnLabel, LineNumberLabel, SurfaceLabel
from ebl.text.line import TextLine
from ebl.text.reconstructed_text import AkkadianWord, Caesura, EnclosurePart, \
    Lacuna, LacunaPart, MetricalFootSeparator, Modifier, SeparatorPart, \
    StringPart
from ebl.text.token import Word


class ManuscriptFactory(factory.Factory):
    class Meta:
        model = Manuscript

    id = factory.Sequence(lambda n: n)
    siglum_disambiguator = factory.Faker('word')
    museum_number =\
        factory.Sequence(lambda n: f'M.{n}' if pydash.is_odd(n) else '')
    accession =\
        factory.Sequence(lambda n: f'A.{n}' if pydash.is_even(n) else '')
    period_modifier = factory.fuzzy.FuzzyChoice(PeriodModifier)
    period = factory.fuzzy.FuzzyChoice(Period)
    provenance = factory.fuzzy.FuzzyChoice(Provenance)
    type = factory.fuzzy.FuzzyChoice(ManuscriptType)
    notes = factory.Faker('sentence')
    references = factory.List([
        factory.SubFactory(ReferenceWithDocumentFactory)
    ], TupleFactory)


class ManuscriptLineFactory(factory.Factory):
    class Meta:
        model = ManuscriptLine

    manuscript_id = factory.Sequence(lambda n: n)
    labels = (
        SurfaceLabel.from_label(Surface.OBVERSE),
        ColumnLabel.from_label('iii', [Status.COLLATION, Status.CORRECTION])
    )
    line = TextLine('1.', (
        Word('ku]-nu-ši'),
    ))


class LineFactory(factory.Factory):
    class Meta:
        model = Line

    number = factory.Sequence(lambda n: LineNumberLabel(str(n)))
    reconstruction = (AkkadianWord((StringPart('buāru'),)),
                      MetricalFootSeparator(True),
                      Lacuna((Enclosure(EnclosureType.BROKEN_OFF,
                                        EnclosureVariant.OPEN), ),
                             tuple()),
                      Caesura(False),
                      AkkadianWord((LacunaPart(),
                                    EnclosurePart(Enclosure(
                                        EnclosureType.BROKEN_OFF,
                                        EnclosureVariant.CLOSE
                                    )),
                                    SeparatorPart(),
                                    StringPart('buāru')),
                                   (Modifier.DAMAGED, )))
    manuscripts: Tuple[ManuscriptLine, ...] = factory.List([
        factory.SubFactory(ManuscriptLineFactory)
    ], TupleFactory)


class ChapterFactory(factory.Factory):
    class Meta:
        model = Chapter

    classification = factory.fuzzy.FuzzyChoice(Classification)
    stage = factory.fuzzy.FuzzyChoice(Stage)
    version = factory.Faker('word')
    name = factory.Faker('sentence')
    order = factory.Faker('pyint')
    manuscripts = factory.List([
        factory.SubFactory(ManuscriptFactory)
    ], TupleFactory)
    lines = factory.List([
        factory.SubFactory(LineFactory)
    ], TupleFactory)


class TextFactory(factory.Factory):
    class Meta:
        model = Text

    category = factory.Sequence(lambda n: n)
    index = factory.Sequence(lambda n: n)
    name = factory.Faker('sentence')
    number_of_verses = factory.fuzzy.FuzzyInteger(1, 10000)
    approximate_verses = factory.Iterator([True, False])
    chapters = factory.List([
        factory.SubFactory(ChapterFactory)
    ], TupleFactory)
