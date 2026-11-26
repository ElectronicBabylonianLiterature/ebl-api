from factory.base import Factory
from factory.declarations import Sequence, SubFactory
from factory.faker import Faker
from factory.fuzzy import FuzzyChoice
from ebl.tests.factories.factory_meta import FactoryMeta

from ebl.tests.factories.ids import ChapterNameFactory, TextIdFactory
from ebl.transliteration.domain.atf import Surface
from ebl.transliteration.domain.labels import SurfaceLabel
from ebl.transliteration.domain.line_number import LineNumber
from ebl.transliteration.domain.museum_number import MuseumNumber

from ebl.transliteration.domain.parallel_line import (
    Labels,
    ParallelComposition,
    ParallelFragment,
    ParallelText,
)


class LabelsFactory(Factory):
    class Meta(FactoryMeta):
        model = Labels

    object = None
    surface = FuzzyChoice([None, SurfaceLabel.from_label(Surface.OBVERSE)])
    column = None


class ParallelFragmentFactory(Factory):
    class Meta(FactoryMeta):
        model = ParallelFragment

    has_cf = Faker("boolean")
    museum_number = Sequence(lambda n: MuseumNumber("X", str(n)))
    has_duplicates = Faker("boolean")
    labels = SubFactory(LabelsFactory)
    line_number = LineNumber(1)
    exists = None


class ParallelTextFactory(Factory):
    class Meta(FactoryMeta):
        model = ParallelText

    has_cf = Faker("boolean")
    text = SubFactory(TextIdFactory)
    chapter = SubFactory(ChapterNameFactory)
    line_number = LineNumber(1)
    exists = None
    implicit_chapter = None


class ParallelCompositionFactory(Factory):
    class Meta(FactoryMeta):
        model = ParallelComposition

    has_cf = Faker("boolean")
    name = Faker("sentence")
    line_number = LineNumber(1)
