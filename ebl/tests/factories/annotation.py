from factory.base import Factory
from factory.declarations import List, Sequence, SubFactory
from factory.faker import Faker
from factory.fuzzy import FuzzyFloat
from ebl.tests.factories.factory_meta import FactoryMeta

from ebl.fragmentarium.application.cropped_sign_image import CroppedSign
from ebl.fragmentarium.domain.annotation import (
    Annotation,
    AnnotationData,
    Annotations,
    Geometry,
    AnnotationValueType,
)
from ebl.tests.factories.fragment import ScriptFactory
from ebl.transliteration.domain.museum_number import MuseumNumber


class GeometryFactory(Factory):
    class Meta(FactoryMeta):
        model = Geometry

    x = FuzzyFloat(0, 100)
    y = FuzzyFloat(0, 100)
    width = FuzzyFloat(10, 100)
    height = FuzzyFloat(10, 100)


class AnnotationDataFactory(Factory):
    class Meta(FactoryMeta):
        model = AnnotationData

    id = Sequence(lambda n: f"annotation-{n}")
    type = AnnotationValueType.HAS_SIGN
    sign_name = Faker("word")
    value = Faker("word")
    path = List(
        [
            Faker("random_int", min=0, max=10),
            Faker("random_int", min=0, max=10),
            Faker("random_int", min=0, max=10),
        ]
    )


class CroppedSignFactory(Factory):
    class Meta(FactoryMeta):
        model = CroppedSign

    image_id = Faker("word")
    label = Faker("word")


class AnnotationFactory(Factory):
    class Meta(FactoryMeta):
        model = Annotation

    geometry = SubFactory(GeometryFactory)
    data = SubFactory(AnnotationDataFactory)
    cropped_sign = SubFactory(CroppedSignFactory)


class AnnotationsFactory(Factory):
    class Meta(FactoryMeta):
        model = Annotations

    fragment_number = Sequence(lambda n: MuseumNumber("X", str(n)))
    annotations = List([SubFactory(AnnotationFactory), SubFactory(AnnotationFactory)])


class AnnotationsWithScriptFactory(AnnotationsFactory):
    script = SubFactory(ScriptFactory)
