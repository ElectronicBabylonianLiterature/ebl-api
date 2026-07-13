import pytest

from ebl.fragmentarium.domain.named_entity import RealiaEntity
from ebl.tests.factories.fragment import TransliteratedFragmentFactory


@pytest.fixture
def entity_annotated_fragment(named_entity_spans):
    fragment = TransliteratedFragmentFactory.build().set_token_ids()

    return fragment.set_named_entities(named_entity_spans)


@pytest.fixture
def mixed_annotated_fragment(mixed_annotation_spans):
    fragment = TransliteratedFragmentFactory.build().set_token_ids()

    return fragment.set_named_entities(mixed_annotation_spans)


def test_named_entities(entity_annotated_fragment, named_entity_spans):
    expected = tuple(span.to_named_entity() for span in named_entity_spans)
    assert entity_annotated_fragment.named_entities == expected


@pytest.mark.parametrize(
    "word_id,expected",
    [
        ("Word-2", ["Entity-1", "Entity-2"]),
        ("Word-3", ["Entity-2"]),
        ("Word-7", ["Entity-3"]),
        ("Word-14", ["Entity-3"]),
    ],
)
def test_word_entities(entity_annotated_fragment, word_id, expected):
    assert entity_annotated_fragment.get_word_by_id(word_id).named_entities == expected


def test_realia_annotation_span_to_named_entity(realia_annotation_spans):
    assert realia_annotation_spans[0].to_named_entity() == RealiaEntity(
        "Realia-1", "realia_000846"
    )


def test_mixed_named_entities(mixed_annotated_fragment, mixed_annotation_spans):
    expected = tuple(span.to_named_entity() for span in mixed_annotation_spans)
    assert mixed_annotated_fragment.named_entities == expected


@pytest.mark.parametrize(
    "word_id,expected",
    [
        ("Word-2", ["Entity-1", "Entity-2", "Realia-1"]),
        ("Word-3", ["Entity-2", "Realia-1"]),
        ("Word-7", ["Entity-3", "Realia-2"]),
        ("Word-14", ["Entity-3"]),
    ],
)
def test_realia_ids_share_word_named_entities(
    mixed_annotated_fragment, word_id, expected
):
    assert mixed_annotated_fragment.get_word_by_id(word_id).named_entities == expected


def test_overlapping_spans_share_token_range(overlapping_annotation_spans):
    fragment = (
        TransliteratedFragmentFactory.build()
        .set_token_ids()
        .set_named_entities(overlapping_annotation_spans)
    )

    for word_id in ["Word-2", "Word-3"]:
        assert fragment.get_word_by_id(word_id).named_entities == [
            "Entity-1",
            "Realia-1",
        ]


def test_deleting_realia_span_clears_word_named_entities(
    mixed_annotated_fragment, named_entity_spans
):
    updated = mixed_annotated_fragment.set_named_entities(named_entity_spans)

    assert all(
        "Realia-1" not in word.named_entities and "Realia-2" not in word.named_entities
        for word in updated.words
    )
    assert updated.named_entities == tuple(
        span.to_named_entity() for span in named_entity_spans
    )
