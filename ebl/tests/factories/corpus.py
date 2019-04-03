import factory
import factory.fuzzy
from ebl.corpus.text import Text, Chapter, Classification, Stage
from ebl.tests.factories.collections import TupleFactory


class ChapterFactory(factory.Factory):
    class Meta:
        model = Chapter

    classification = factory.fuzzy.FuzzyChoice(Classification)
    stage = factory.fuzzy.FuzzyChoice(Stage)
    number = factory.fuzzy.FuzzyInteger(1)


class TextFactory(factory.Factory):
    class Meta:
        model = Text

    category = factory.fuzzy.FuzzyInteger(1)
    index = factory.fuzzy.FuzzyInteger(1)
    name = factory.Faker('sentence')
    chapters = factory.List([
        factory.SubFactory(ChapterFactory)
    ], TupleFactory)
