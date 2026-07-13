import pytest

from ebl.fragmentarium.domain.named_entity import (
    EntityAnnotationSpan,
    NamedEntityType,
    RealiaAnnotationSpan,
    deduplicate_spans,
)
from ebl.tests.factories.fragment import TransliteratedFragmentFactory
from ebl.tests.fragmentarium.conftest import KNOWN_REALIA_ID, OTHER_REALIA_ID

PERSON_ON_WORD_2 = EntityAnnotationSpan(
    "Entity-1", NamedEntityType.PERSONAL_NAME, ["Word-2"]
)
REALIA_ON_WORD_2 = RealiaAnnotationSpan("Realia-1", KNOWN_REALIA_ID, ["Word-2"])


def test_duplicate_entity_on_same_span_is_dropped():
    duplicate = EntityAnnotationSpan(
        "Entity-2", NamedEntityType.PERSONAL_NAME, ["Word-2"]
    )

    assert deduplicate_spans([PERSON_ON_WORD_2, duplicate]) == [PERSON_ON_WORD_2]


def test_duplicate_realia_on_same_span_is_dropped():
    duplicate = RealiaAnnotationSpan("Realia-2", KNOWN_REALIA_ID, ["Word-2"])

    assert deduplicate_spans([REALIA_ON_WORD_2, duplicate]) == [REALIA_ON_WORD_2]


def test_span_order_does_not_defeat_deduplication():
    span = EntityAnnotationSpan(
        "Entity-1", NamedEntityType.PERSONAL_NAME, ["Word-2", "Word-3"]
    )
    reordered = EntityAnnotationSpan(
        "Entity-2", NamedEntityType.PERSONAL_NAME, ["Word-3", "Word-2"]
    )

    assert deduplicate_spans([span, reordered]) == [span]


def test_first_occurrence_is_kept():
    duplicate = EntityAnnotationSpan(
        "Entity-2", NamedEntityType.PERSONAL_NAME, ["Word-2"]
    )

    assert deduplicate_spans([PERSON_ON_WORD_2, duplicate])[0].id == "Entity-1"


@pytest.mark.parametrize(
    "other",
    [
        pytest.param(
            EntityAnnotationSpan("Entity-2", NamedEntityType.PERSONAL_NAME, ["Word-3"]),
            id="same_type_different_span",
        ),
        pytest.param(
            EntityAnnotationSpan("Entity-2", NamedEntityType.DIVINE_NAME, ["Word-2"]),
            id="different_type_same_span",
        ),
    ],
)
def test_distinct_entities_are_kept(other):
    assert deduplicate_spans([PERSON_ON_WORD_2, other]) == [PERSON_ON_WORD_2, other]


@pytest.mark.parametrize(
    "other",
    [
        pytest.param(
            RealiaAnnotationSpan("Realia-2", KNOWN_REALIA_ID, ["Word-3"]),
            id="same_realia_different_span",
        ),
        pytest.param(
            RealiaAnnotationSpan("Realia-2", OTHER_REALIA_ID, ["Word-2"]),
            id="different_realia_same_span",
        ),
    ],
)
def test_distinct_realia_are_kept(other):
    assert deduplicate_spans([REALIA_ON_WORD_2, other]) == [REALIA_ON_WORD_2, other]


def test_empty_spans():
    assert deduplicate_spans([]) == []


def test_fragment_never_stores_duplicates():
    duplicate = EntityAnnotationSpan(
        "Entity-2", NamedEntityType.PERSONAL_NAME, ["Word-2"]
    )
    fragment = (
        TransliteratedFragmentFactory.build()
        .set_token_ids()
        .set_named_entities([PERSON_ON_WORD_2, duplicate], [REALIA_ON_WORD_2])
    )

    assert fragment.named_entities == (PERSON_ON_WORD_2.to_named_entity(),)
    assert fragment.realia == (REALIA_ON_WORD_2.to_realia_entity(),)
    assert fragment.get_word_by_id("Word-2").named_entities == ["Entity-1"]
    assert fragment.get_word_by_id("Word-2").realia == ["Realia-1"]
