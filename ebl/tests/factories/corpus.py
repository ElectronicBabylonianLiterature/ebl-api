# pylint: disable=R0903
from typing import Tuple

import factory.fuzzy
import pydash

from ebl.corpus.text import (Chapter, Manuscript,
                             Text, Line, ManuscriptLine)
from ebl.corpus.enums import Classification, ManuscriptType, Provenance, \
    PeriodModifier, Period, Stage
from ebl.tests.factories.bibliography import ReferenceWithDocumentFactory
from ebl.tests.factories.collections import TupleFactory
from ebl.text.atf import Surface, Status
from ebl.text.labels import SurfaceLabel, ColumnLabel, LineNumberLabel
from ebl.text.line import TextLine
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
        Word('-ku]-nu-ši'),
    ))


class LineFactory(factory.Factory):
    class Meta:
        model = Line

    number = factory.Sequence(lambda n: LineNumberLabel(str(n)))
    reconstruction = factory.Faker('sentence')
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

    category = factory.fuzzy.FuzzyInteger(0)
    index = factory.fuzzy.FuzzyInteger(0)
    name = factory.Faker('sentence')
    number_of_verses = factory.fuzzy.FuzzyInteger(1, 10000)
    approximate_verses = factory.Iterator([True, False])
    chapters = factory.List([
        factory.SubFactory(ChapterFactory)
    ], TupleFactory)
