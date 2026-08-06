from ebl.dictionary.domain.word import WordId
from freezegun import freeze_time
import pytest

from ebl.errors import NotFoundError
from ebl.fragmentarium.application.fragment_updater import FragmentUpdater
from ebl.fragmentarium.domain.fragment import Fragment
from ebl.lemmatization.domain.lemmatization import Lemmatization, LemmatizationToken
from ebl.tests.factories.fragment import FragmentFactory, TransliteratedFragmentFactory
from ebl.tests.fragmentarium.fragment_updater_test_helpers import (
    FROZEN_TIME,
    UpdaterContext,
)


@freeze_time(FROZEN_TIME)
def test_update_lemmatization(fragment_updater, updater_context: UpdaterContext):
    transliterated_fragment = TransliteratedFragmentFactory.build()
    number = transliterated_fragment.number
    tokens = [list(line) for line in transliterated_fragment.text.lemmatization.tokens]
    tokens[1][3] = LemmatizationToken(tokens[1][3].value, (WordId("aklu I"),))
    lemmatization = Lemmatization(tokens)
    lemmatized_fragment = transliterated_fragment.update_lemmatization(lemmatization)
    updater_context.expect_query(number, transliterated_fragment)
    injected_fragment = updater_context.inject(lemmatized_fragment)
    updater_context.expect_changelog(
        number, transliterated_fragment, lemmatized_fragment
    )
    updater_context.expect_update_field("lemmatization", lemmatized_fragment)

    result = fragment_updater.update_lemmatization(
        number, lemmatization, updater_context.user
    )
    assert result == (injected_fragment, False)


def test_update_update_lemmatization_not_found(
    fragment_updater, user, fragment_repository, when
):
    number = "K.1"
    (when(fragment_repository).query_by_museum_number(number).thenRaise(NotFoundError))

    with pytest.raises(NotFoundError):
        fragment_updater.update_lemmatization(
            number, Lemmatization(((LemmatizationToken("1.", ()),),)), user
        )


@pytest.mark.parametrize(
    "field,value",
    [("introduction", "Test introduction"), ("notes", "Test notes")],
)
def test_update_edition_metadata_field(
    field,
    value,
    fragment_updater: FragmentUpdater,
    updater_context: UpdaterContext,
):
    fragment: Fragment = FragmentFactory.build()
    number = fragment.number
    updated_fragment = getattr(fragment, f"set_{field}")(value)
    updater_context.expect_query(number, fragment)
    updater_context.expect_changelog(number, fragment, updated_fragment)
    updater_context.expect_update_field(field, updated_fragment)

    result = fragment_updater.update_edition(
        number, updater_context.user, **{field: value}
    )
    assert result == (updated_fragment, False)


@freeze_time(FROZEN_TIME)
def test_update_lemma_annotation(fragment_updater, updater_context: UpdaterContext):
    transliterated_fragment = TransliteratedFragmentFactory.build()
    number = transliterated_fragment.number

    annotation = {1: {3: ["aklu I"]}}
    lemmatized_fragment = transliterated_fragment.update_lemma_annotation(annotation)

    updater_context.expect_query(number, transliterated_fragment)
    injected_fragment = updater_context.inject(lemmatized_fragment)
    updater_context.expect_changelog(
        number, transliterated_fragment, lemmatized_fragment
    )
    updater_context.expect_update_field("lemmatization", lemmatized_fragment)

    result = fragment_updater.update_lemma_annotation(
        number, annotation, updater_context.user
    )
    assert result == (injected_fragment, False)


@freeze_time(FROZEN_TIME)
def test_update_named_entities(
    fragment_updater, named_entity_spans, updater_context: UpdaterContext
):
    transliterated_fragment: Fragment = TransliteratedFragmentFactory.build()
    number = transliterated_fragment.number

    annotated_fragment = transliterated_fragment.set_named_entities(named_entity_spans)

    updater_context.expect_query(number, transliterated_fragment)
    injected_fragment = updater_context.inject(annotated_fragment)
    updater_context.expect_changelog(
        number, transliterated_fragment, annotated_fragment
    )
    updater_context.expect_update_field("named_entities", annotated_fragment)

    result = fragment_updater.update_named_entities(
        number, named_entity_spans, [], updater_context.user
    )
    assert result == (injected_fragment, False)
