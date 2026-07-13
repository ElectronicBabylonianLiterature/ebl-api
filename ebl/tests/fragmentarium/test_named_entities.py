import pytest

from ebl.fragmentarium.domain.named_entity import RealiaEntity
from ebl.tests.factories.fragment import TransliteratedFragmentFactory


@pytest.fixture
def entity_annotated_fragment(named_entity_spans):
    fragment = TransliteratedFragmentFactory.build().set_token_ids()

    return fragment.set_named_entities(named_entity_spans)


@pytest.fixture
def fully_annotated_fragment(named_entity_spans, realia_annotation_spans):
    fragment = TransliteratedFragmentFactory.build().set_token_ids()

    return fragment.set_named_entities(named_entity_spans, realia_annotation_spans)


def test_named_entities(entity_annotated_fragment, named_entity_spans):
    expected = tuple(span.to_named_entity() for span in named_entity_spans)
    assert entity_annotated_fragment.named_entities == expected


def test_realia_defaults_to_empty(entity_annotated_fragment):
    assert entity_annotated_fragment.realia == ()
    assert all(word.realia == [] for word in entity_annotated_fragment.words)


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


def test_realia_annotation_span_to_realia_entity(realia_annotation_spans):
    assert realia_annotation_spans[0].to_realia_entity() == RealiaEntity(
        "Realia-1", "realia_000846"
    )


def test_realia_entities(fully_annotated_fragment, realia_annotation_spans):
    expected = tuple(span.to_realia_entity() for span in realia_annotation_spans)
    assert fully_annotated_fragment.realia == expected


def test_named_entities_unaffected_by_realia(
    fully_annotated_fragment, named_entity_spans
):
    expected = tuple(span.to_named_entity() for span in named_entity_spans)
    assert fully_annotated_fragment.named_entities == expected


@pytest.mark.parametrize(
    "word_id,tags,realia",
    [
        ("Word-2", ["Entity-1", "Entity-2"], ["Realia-1"]),
        ("Word-3", ["Entity-2"], ["Realia-1"]),
        ("Word-7", ["Entity-3"], ["Realia-2"]),
        ("Word-14", ["Entity-3"], []),
    ],
)
def test_kinds_are_never_intermixed(fully_annotated_fragment, word_id, tags, realia):
    word = fully_annotated_fragment.get_word_by_id(word_id)

    assert word.named_entities == tags
    assert word.realia == realia
    assert not set(word.named_entities) & set(word.realia)


def test_deleting_realia_keeps_named_entities(
    fully_annotated_fragment, named_entity_spans
):
    updated = fully_annotated_fragment.set_named_entities(named_entity_spans, [])

    assert updated.realia == ()
    assert all(word.realia == [] for word in updated.words)
    assert updated.named_entities == tuple(
        span.to_named_entity() for span in named_entity_spans
    )


def test_deleting_named_entities_keeps_realia(
    fully_annotated_fragment, realia_annotation_spans
):
    updated = fully_annotated_fragment.set_named_entities([], realia_annotation_spans)

    assert updated.named_entities == ()
    assert all(word.named_entities == [] for word in updated.words)
    assert updated.realia == tuple(
        span.to_realia_entity() for span in realia_annotation_spans
    )
