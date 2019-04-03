import factory
import factory.fuzzy
from ebl.corpus.text import (
    Text, Chapter, Manuscript, Classification, Stage, Period, Provenance,
    ManuscriptType
)
from ebl.tests.factories.collections import TupleFactory


class Manuscript(factory.Factory):
    class Meta:
        model = Manuscript

    siglum = factory.Faker('word')
    museum_number = factory.Sequence(lambda n: f'M.{n}')
    accession = factory.Sequence(lambda n: f'A.{n}')
    period = factory.fuzzy.FuzzyChoice(Period)
    provenance = factory.fuzzy.FuzzyChoice(Provenance)
    type = factory.fuzzy.FuzzyChoice(ManuscriptType)


class ChapterFactory(factory.Factory):
    class Meta:
        model = Chapter

    classification = factory.fuzzy.FuzzyChoice(Classification)
    stage = factory.fuzzy.FuzzyChoice(Stage)
    number = factory.fuzzy.FuzzyInteger(1)
    manuscripts = factory.List([
        factory.SubFactory(Manuscript)
    ], TupleFactory)


class TextFactory(factory.Factory):
    class Meta:
        model = Text

    category = factory.fuzzy.FuzzyInteger(1)
    index = factory.fuzzy.FuzzyInteger(1)
    name = factory.Faker('sentence')
    chapters = factory.List([
        factory.SubFactory(ChapterFactory)
    ], TupleFactory)
