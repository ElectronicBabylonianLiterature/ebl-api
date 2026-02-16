import factory

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


class LabelsFactory(factory.Factory):
    class Meta:
        model = Labels

    object = None
    surface = factory.fuzzy.FuzzyChoice(
        [None, SurfaceLabel.from_label(Surface.OBVERSE)]
    )
    column = None


class ParallelFragmentFactory(factory.Factory):
    class Meta:
        model = ParallelFragment

    has_cf = factory.Faker("boolean")
    museum_number = factory.Sequence(lambda n: MuseumNumber("X", str(n)))
    has_duplicates = factory.Faker("boolean")
    labels = factory.SubFactory(LabelsFactory)
    line_number = LineNumber(1)
    exists = None


class ParallelTextFactory(factory.Factory):
    class Meta:
        model = ParallelText

    has_cf = factory.Faker("boolean")
    text = factory.SubFactory(TextIdFactory)
    chapter = factory.SubFactory(ChapterNameFactory)
    line_number = LineNumber(1)
    exists = None
    implicit_chapter = None


class ParallelCompositionFactory(factory.Factory):
    class Meta:
        model = ParallelComposition

    has_cf = factory.Faker("boolean")
    name = factory.Faker("sentence")
    line_number = LineNumber(1)
