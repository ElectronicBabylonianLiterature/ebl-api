from ebl.fragmentarium.application.named_entity_schema import (
    EntityAnnotationSpanSchema,
    NamedEntitySchema,
)
import pytest

from ebl.fragmentarium.domain.named_entity import (
    EntityAnnotationSpan,
    NamedEntity,
    NamedEntityType,
)


@pytest.mark.parametrize(
    "entity,serialized",
    [
        (
            NamedEntity("Test-1", NamedEntityType.GEOGRAPHICAL_NAME),
            {"id": "Test-1", "type": NamedEntityType.GEOGRAPHICAL_NAME.long_name},
        ),
        (
            NamedEntity("Test-2", NamedEntityType.PERSONAL_NAME),
            {"id": "Test-2", "type": NamedEntityType.PERSONAL_NAME.long_name},
        ),
    ],
)
def test_named_entity_schema(entity, serialized):
    assert NamedEntitySchema().load(serialized) == entity
    assert NamedEntitySchema().dump(entity) == serialized


@pytest.mark.parametrize(
    "span,serialized",
    [
        (
            EntityAnnotationSpan(
                "Test-1", NamedEntityType.YEAR_NAME, ["Word-1", "Word-2"]
            ),
            {
                "id": "Test-1",
                "type": NamedEntityType.YEAR_NAME.long_name,
                "span": ["Word-1", "Word-2"],
            },
        ),
        (
            EntityAnnotationSpan(
                "Test-2", NamedEntityType.PERSONAL_NAME, ["Word-3", "Word-4"]
            ),
            {
                "id": "Test-2",
                "type": NamedEntityType.PERSONAL_NAME.long_name,
                "span": ["Word-3", "Word-4"],
            },
        ),
    ],
)
def test_entity_annotation_span_schema(span, serialized):
    assert EntityAnnotationSpanSchema().load(serialized) == span
    assert EntityAnnotationSpanSchema().dump(span) == serialized
