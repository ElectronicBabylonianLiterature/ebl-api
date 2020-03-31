import factory  # pyre-ignore.fuzzy  # pyre-ignore

from ebl.fragmentarium.domain.annotation import (
    Annotation,
    AnnotationData,
    Annotations,
    Geometry,
)


class GeometryFactory(factory.Factory):  # pyre-ignore[11]
    class Meta:
        model = Geometry

    x = factory.fuzzy.FuzzyFloat(0, 100)
    y = factory.fuzzy.FuzzyFloat(0, 100)
    width = factory.fuzzy.FuzzyFloat(0, 100)
    height = factory.fuzzy.FuzzyFloat(0, 100)


class AnnotationDataFactory(factory.Factory):  # pyre-ignore[11]
    class Meta:
        model = AnnotationData

    id = factory.Sequence(lambda n: f"annotation-{n}")
    value = factory.Faker("word")
    path = factory.List(
        [
            factory.Faker("random_int", min=0),
            factory.Faker("random_int", min=0),
            factory.Faker("random_int", min=0),
        ]
    )


class AnnotationFactory(factory.Factory):  # pyre-ignore[11]
    class Meta:
        model = Annotation

    geometry = factory.SubFactory(GeometryFactory)
    data = factory.SubFactory(AnnotationDataFactory)


class AnnotationsFactory(factory.Factory):  # pyre-ignore[11]
    class Meta:
        model = Annotations

    fragment_number = factory.Sequence(lambda n: f"X.{n}")
    annotations = factory.List(
        [factory.SubFactory(AnnotationFactory), factory.SubFactory(AnnotationFactory),]
    )
