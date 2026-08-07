import pytest

from ebl.fragmentarium.domain.fragment import Fragment
from ebl.fragmentarium.domain.named_entity import (
    EntityAnnotationSpan,
    NamedEntityType,
    RealiaAnnotationSpan,
)
from ebl.fragmentarium.domain.transliteration_update import TransliterationUpdate
from ebl.transliteration.domain.atf_parsers.lark_parser import parse_atf_lark
from ebl.transliteration.domain.museum_number import MuseumNumber
from ebl.users.domain.user import Guest

ATF = "1. ku-nu-uk ba-bi-lu a-na"
REALIA_ID = "realia_000846"


@pytest.fixture
def annotated_fragment() -> Fragment:
    fragment = Fragment(
        number=MuseumNumber.of("X.1"), text=parse_atf_lark(ATF)
    ).set_token_ids()
    word_ids = [word.id_ for word in fragment.words if word.id_]

    return fragment.set_named_entities(
        [
            EntityAnnotationSpan(
                "Entity-1", NamedEntityType.PERSONAL_NAME, [word_ids[0]]
            ),
            EntityAnnotationSpan("Entity-2", NamedEntityType.ROYAL_NAME, [word_ids[2]]),
        ],
        [RealiaAnnotationSpan("Realia-1", REALIA_ID, [word_ids[1]])],
    )


def update(fragment: Fragment, atf: str) -> Fragment:
    return fragment.update_transliteration(
        TransliterationUpdate(parse_atf_lark(atf)), Guest()
    )


def test_unchanged_words_keep_their_annotations(annotated_fragment):
    updated = update(annotated_fragment, "1. ku-nu-uk ba-bi-lu szu-nu")

    words = {word.clean_value: word for word in updated.words}
    assert list(words["ku-nu-uk"].named_entities) == ["Entity-1"]
    assert list(words["ba-bi-lu"].realia) == ["Realia-1"]


def test_changed_word_loses_its_annotation(annotated_fragment):
    updated = update(annotated_fragment, "1. ku-nu-uk ba-bi-lu szu-nu")

    words = {word.clean_value: word for word in updated.words}
    assert list(words["szu-nu"].named_entities) == []
    assert list(words["szu-nu"].realia) == []


def test_orphaned_named_entity_is_dropped(annotated_fragment):
    updated = update(annotated_fragment, "1. ku-nu-uk ba-bi-lu szu-nu")

    assert [entity.id for entity in updated.named_entities] == ["Entity-1"]


def test_orphaned_realia_is_dropped(annotated_fragment):
    updated = update(annotated_fragment, "1. ku-nu-uk szu-nu a-na")

    assert updated.realia == ()
    assert [entity.id for entity in updated.named_entities] == [
        "Entity-1",
        "Entity-2",
    ]


def test_unrelated_change_keeps_every_annotation(annotated_fragment):
    updated = update(annotated_fragment, f"{ATF}\n2. szu-nu")

    assert [entity.id for entity in updated.named_entities] == [
        "Entity-1",
        "Entity-2",
    ]
    assert [entity.realia_id for entity in updated.realia] == [REALIA_ID]


def test_pruned_annotations_are_persisted(fragment_repository, annotated_fragment):
    fragment_repository.create(annotated_fragment)
    updated = update(annotated_fragment, "1. ku-nu-uk ba-bi-lu szu-nu")

    fragment_repository.update_field("transliteration", updated)

    stored = fragment_repository.query_by_museum_number(annotated_fragment.number)
    assert [entity.id for entity in stored.named_entities] == ["Entity-1"]
    assert [entity.id for entity in stored.realia] == ["Realia-1"]


def test_replacing_every_word_drops_every_annotation(annotated_fragment):
    updated = update(annotated_fragment, "1. szu-nu li-ib-bu qa-tu")

    assert updated.named_entities == ()
    assert updated.realia == ()
