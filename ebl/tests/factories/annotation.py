import factory.fuzzy

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


class GeometryFactory(factory.Factory):
    class Meta:
        model = Geometry

    x = factory.fuzzy.FuzzyFloat(0, 100)
    y = factory.fuzzy.FuzzyFloat(0, 100)
    width = factory.fuzzy.FuzzyFloat(10, 100)
    height = factory.fuzzy.FuzzyFloat(10, 100)


class AnnotationDataFactory(factory.Factory):
    class Meta:
        model = AnnotationData

    id = factory.Sequence(lambda n: f"annotation-{n}")
    type = AnnotationValueType.HAS_SIGN
    sign_name = factory.Faker("word")
    value = factory.Faker("word")
    path = factory.List(
        [
            factory.Faker("random_int", min=0, max=10),
            factory.Faker("random_int", min=0, max=10),
            factory.Faker("random_int", min=0, max=10),
        ]
    )


class CroppedSignFactory(factory.Factory):
    class Meta:
        model = CroppedSign

    image_id = factory.Faker("word")
    label = factory.Faker("word")


class AnnotationFactory(factory.Factory):
    class Meta:
        model = Annotation

    geometry = factory.SubFactory(GeometryFactory)
    data = factory.SubFactory(AnnotationDataFactory)
    cropped_sign = factory.SubFactory(CroppedSignFactory)


class AnnotationsFactory(factory.Factory):
    class Meta:
        model = Annotations

    fragment_number = factory.Sequence(lambda n: MuseumNumber("X", str(n)))
    annotations = factory.List(
        [factory.SubFactory(AnnotationFactory), factory.SubFactory(AnnotationFactory)]
    )


class AnnotationsWithScriptFactory(AnnotationsFactory):
    script = factory.SubFactory(ScriptFactory)
