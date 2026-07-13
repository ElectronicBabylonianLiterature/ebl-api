import pytest
from marshmallow import ValidationError

from ebl.fragmentarium.application.named_entity_schema import (
    EntityAnnotationSpanSchema,
    NamedEntitySchema,
    RealiaAnnotationSpanSchema,
    RealiaEntitySchema,
)
from ebl.fragmentarium.domain.named_entity import (
    EntityAnnotationSpan,
    NamedEntity,
    NamedEntityType,
    RealiaAnnotationSpan,
    RealiaEntity,
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


@pytest.mark.parametrize(
    "entity,serialized",
    [
        (
            RealiaEntity("Realia-1", "realia_000846"),
            {"id": "Realia-1", "realiaId": "realia_000846"},
        ),
        (
            RealiaEntity("Realia-2", "realia_1"),
            {"id": "Realia-2", "realiaId": "realia_1"},
        ),
    ],
)
def test_realia_entity_schema(entity, serialized):
    assert RealiaEntitySchema().load(serialized) == entity
    assert RealiaEntitySchema().dump(entity) == serialized


def test_realia_annotation_span_schema():
    span = RealiaAnnotationSpan("Realia-1", "realia_000846", ["Word-1", "Word-2"])
    serialized = {
        "id": "Realia-1",
        "realiaId": "realia_000846",
        "span": ["Word-1", "Word-2"],
    }
    assert RealiaAnnotationSpanSchema().load(serialized) == span
    assert RealiaAnnotationSpanSchema().dump(span) == serialized


@pytest.mark.parametrize(
    "serialized",
    [
        pytest.param(
            {"id": "X", "realiaId": "realia_1", "span": ["Word-1"]},
            id="realia_id_on_entity_schema",
        ),
        pytest.param({"id": "X", "span": ["Word-1"]}, id="missing_type"),
        pytest.param(
            {"id": "X", "type": "PERSONAL_NAME", "span": ["Word-1"], "tier": 1},
            id="unknown_key",
        ),
    ],
)
def test_entity_span_schema_rejects(serialized):
    with pytest.raises(ValidationError):
        EntityAnnotationSpanSchema().load(serialized)


@pytest.mark.parametrize(
    "serialized",
    [
        pytest.param(
            {"id": "X", "type": "PERSONAL_NAME", "span": ["Word-1"]},
            id="type_on_realia_schema",
        ),
        pytest.param({"id": "X", "span": ["Word-1"]}, id="missing_realia_id"),
        pytest.param(
            {"id": "X", "realiaId": "Apkallu", "span": ["Word-1"]}, id="lemma_id"
        ),
        pytest.param(
            {"id": "X", "realiaId": "realia_", "span": ["Word-1"]}, id="no_digits"
        ),
        pytest.param(
            {"id": "X", "realiaId": "realia_abc", "span": ["Word-1"]}, id="non_numeric"
        ),
        pytest.param(
            {"id": "X", "realiaId": "realia_1", "span": ["Word-1"], "name": "x"},
            id="unknown_key",
        ),
    ],
)
def test_realia_span_schema_rejects(serialized):
    with pytest.raises(ValidationError):
        RealiaAnnotationSpanSchema().load(serialized)
