# pylint: disable=R0903
import factory
import factory.fuzzy
import pydash
from ebl.corpus.text import (
    Text, Chapter, Manuscript, Classification, Stage, Period,
    PeriodModifier, Provenance, ManuscriptType
)
from ebl.tests.factories.bibliography import ReferenceWithDocumentFactory
from ebl.tests.factories.collections import TupleFactory


class ManuscriptFactory(factory.Factory):
    class Meta:
        model = Manuscript

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
