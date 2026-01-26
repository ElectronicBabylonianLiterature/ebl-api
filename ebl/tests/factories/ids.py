import factory
from ebl.transliteration.domain.genre import Genre

from ebl.transliteration.domain.parallel_line import ChapterName
from ebl.common.domain.stage import Stage
from ebl.transliteration.domain.text_id import TextId


class TextIdFactory(factory.Factory):
    class Meta:
        model = TextId

    genre = factory.fuzzy.FuzzyChoice(Genre)
    category = factory.Sequence(lambda n: n)
    index = factory.Sequence(lambda n: n)


class ChapterNameFactory(factory.Factory):
    class Meta:
        model = ChapterName

    stage = factory.fuzzy.FuzzyChoice(Stage)
    version = factory.Faker("sentence")
    name = factory.Faker("sentence")
