from ebl.fragmentarium.application.named_entity_schema import (
    AnnotationEntitySchema,
    AnnotationSpanSchema,
    EntityAnnotationSpanSchema,
    NamedEntitySchema,
    RealiaAnnotationSpanSchema,
    RealiaEntitySchema,
)
import pytest
from marshmallow import ValidationError

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


ENTITY_SPAN = EntityAnnotationSpan(
    "Entity-1", NamedEntityType.PERSONAL_NAME, ["Word-1", "Word-2"]
)
SERIALIZED_ENTITY_SPAN = {
    "id": "Entity-1",
    "type": "PERSONAL_NAME",
    "span": ["Word-1", "Word-2"],
}
REALIA_SPAN = RealiaAnnotationSpan("Realia-1", "realia_000846", ["Word-1", "Word-2"])
SERIALIZED_REALIA_SPAN = {
    "id": "Realia-1",
    "realiaId": "realia_000846",
    "span": ["Word-1", "Word-2"],
}


def test_annotation_span_schema_round_trip():
    serialized = [SERIALIZED_ENTITY_SPAN, SERIALIZED_REALIA_SPAN]
    spans = [ENTITY_SPAN, REALIA_SPAN]

    assert AnnotationSpanSchema().load(serialized, many=True) == spans
    assert AnnotationSpanSchema().dump(spans, many=True) == serialized


def test_annotation_entity_schema_round_trip():
    serialized = [
        {"id": "Entity-1", "type": "PERSONAL_NAME"},
        {"id": "Realia-1", "realiaId": "realia_000846"},
    ]
    entities = [
        NamedEntity("Entity-1", NamedEntityType.PERSONAL_NAME),
        RealiaEntity("Realia-1", "realia_000846"),
    ]

    assert AnnotationEntitySchema().load(serialized, many=True) == entities
    assert AnnotationEntitySchema().dump(entities, many=True) == serialized


def test_annotation_span_schema_validate():
    assert AnnotationSpanSchema(many=True).validate([SERIALIZED_REALIA_SPAN]) == {}


@pytest.mark.parametrize(
    "serialized",
    [
        pytest.param(
            {**SERIALIZED_ENTITY_SPAN, "realiaId": "realia_000846"},
            id="type_and_realia",
        ),
        pytest.param({"id": "X", "span": ["Word-1"]}, id="neither_type_nor_realia"),
        pytest.param({**SERIALIZED_REALIA_SPAN, "realiaId": "Apkallu"}, id="lemma_id"),
        pytest.param({**SERIALIZED_REALIA_SPAN, "realiaId": "realia_"}, id="no_digits"),
        pytest.param(
            {**SERIALIZED_REALIA_SPAN, "realiaId": "realia_abc"}, id="non_numeric"
        ),
        pytest.param(
            {**SERIALIZED_REALIA_SPAN, "realiaId": "Assyrien (Geschichte)"},
            id="lemma_id_with_spaces",
        ),
        pytest.param({**SERIALIZED_REALIA_SPAN, "tier": 1}, id="unknown_key_on_realia"),
        pytest.param(
            {**SERIALIZED_ENTITY_SPAN, "name": "x"}, id="unknown_key_on_entity"
        ),
    ],
)
def test_annotation_span_schema_rejects(serialized):
    with pytest.raises(ValidationError):
        AnnotationSpanSchema().load([serialized], many=True)


@pytest.mark.parametrize(
    "serialized",
    [
        pytest.param(
            {"id": "X", "type": "PERSONAL_NAME", "realiaId": "realia_1"},
            id="type_and_realia",
        ),
        pytest.param({"id": "X"}, id="neither_type_nor_realia"),
        pytest.param({"id": "X", "realiaId": "realia_"}, id="malformed_realia_id"),
    ],
)
def test_annotation_entity_schema_rejects(serialized):
    with pytest.raises(ValidationError):
        AnnotationEntitySchema().load([serialized], many=True)
