import pytest

from ebl.tests.factories.fragment import TransliteratedFragmentFactory


@pytest.fixture
def entity_annotated_fragment(named_entity_spans):
    fragment = TransliteratedFragmentFactory.build().set_token_ids()

    return fragment.set_named_entities(named_entity_spans)


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
