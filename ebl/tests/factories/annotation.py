import factory.fuzzy

from ebl.fragmentarium.domain.annotation import (
    Annotation,
    AnnotationData,
    Annotations,
    Geometry,
    AnnotationValueType,
)
from ebl.fragmentarium.domain.museum_number import MuseumNumber


class GeometryFactory(factory.Factory):
    class Meta:
        model = Geometry

    x = factory.fuzzy.FuzzyFloat(0, 100)
    y = factory.fuzzy.FuzzyFloat(0, 100)
    width = factory.fuzzy.FuzzyFloat(0, 100)
    height = factory.fuzzy.FuzzyFloat(0, 100)


class AnnotationDataFactory(factory.Factory):
    class Meta:
        model = AnnotationData

    id = factory.Sequence(lambda n: f"annotation-{n}")
    type = AnnotationValueType.HASSIGN
    sign_name = factory.Faker("word")
    value = factory.Faker("word")
    path = factory.List(
        [
            factory.Faker("random_int", min=0, max=10),
            factory.Faker("random_int", min=0, max=10),
            factory.Faker("random_int", min=0, max=10),
        ]
    )


class AnnotationFactory(factory.Factory):
    class Meta:
        model = Annotation

    geometry = factory.SubFactory(GeometryFactory)
    data = factory.SubFactory(AnnotationDataFactory)


class AnnotationsFactory(factory.Factory):
    class Meta:
        model = Annotations

    fragment_number = factory.Sequence(lambda n: MuseumNumber("X", str(n)))
    annotations = factory.List(
        [factory.SubFactory(AnnotationFactory), factory.SubFactory(AnnotationFactory)]
    )
