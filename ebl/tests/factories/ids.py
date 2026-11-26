from factory.base import Factory
from factory.declarations import Sequence
from factory.faker import Faker
from factory.fuzzy import FuzzyChoice
from ebl.tests.factories.factory_meta import FactoryMeta
from ebl.transliteration.domain.genre import Genre

from ebl.transliteration.domain.parallel_line import ChapterName
from ebl.common.domain.stage import Stage
from ebl.transliteration.domain.text_id import TextId


class TextIdFactory(Factory):
    class Meta(FactoryMeta):
        model = TextId

    genre = FuzzyChoice(Genre)
    category = Sequence(lambda n: n % 5000)
    index = Sequence(lambda n: n)


class ChapterNameFactory(Factory):
    class Meta(FactoryMeta):
        model = ChapterName

    stage = FuzzyChoice(Stage)
    version = Faker("sentence")
    name = Faker("sentence")
