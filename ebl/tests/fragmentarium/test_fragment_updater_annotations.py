from ebl.dictionary.domain.word import WordId
from freezegun import freeze_time
import pytest

from ebl.errors import DataError, NotFoundError
from ebl.fragmentarium.application.fragment_updater import FragmentUpdater
from ebl.fragmentarium.domain.fragment import Fragment
from ebl.lemmatization.domain.lemmatization import Lemmatization, LemmatizationToken
from ebl.tests.factories.bibliography import ReferenceFactory
from ebl.tests.factories.fragment import FragmentFactory, TransliteratedFragmentFactory
from ebl.tests.fragmentarium.fragment_updater_test_helpers import (
    FROZEN_TIME,
    expect_changelog,
)


@freeze_time(FROZEN_TIME)
def test_update_lemmatization(
    fragment_updater, user, fragment_repository, parallel_line_injector, changelog, when
):
    transliterated_fragment = TransliteratedFragmentFactory.build()
    number = transliterated_fragment.number
    tokens = [list(line) for line in transliterated_fragment.text.lemmatization.tokens]
    tokens[1][3] = LemmatizationToken(tokens[1][3].value, (WordId("aklu I"),))
    lemmatization = Lemmatization(tokens)
    lemmatized_fragment = transliterated_fragment.update_lemmatization(lemmatization)
    (
        when(fragment_repository)
        .query_by_museum_number(number)
        .thenReturn(transliterated_fragment)
    )
    injected_fragment = lemmatized_fragment.set_text(
        parallel_line_injector.inject_transliteration(lemmatized_fragment.text)
    )
    expect_changelog(
        when, changelog, user, number, transliterated_fragment, lemmatized_fragment
    )
    when(fragment_repository).update_field(
        "lemmatization", lemmatized_fragment
    ).thenReturn()

    result = fragment_updater.update_lemmatization(number, lemmatization, user)
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


def test_update_references(
    fragment_updater,
    bibliography,
    user,
    fragment_repository,
    parallel_line_injector,
    changelog,
    when,
):
    fragment = FragmentFactory.build()
    number = fragment.number
    reference = ReferenceFactory.build()
    references = (reference,)
    updated_fragment = fragment.set_references(references)
    injected_fragment = updated_fragment.set_text(
        parallel_line_injector.inject_transliteration(updated_fragment.text)
    )
    when(bibliography).find(reference.id).thenReturn(reference)
    when(fragment_repository).query_by_museum_number(number).thenReturn(
        fragment
    ).thenReturn(updated_fragment)
    when(fragment_repository).update_field("references", updated_fragment).thenReturn()
    expect_changelog(when, changelog, user, number, fragment, updated_fragment)

    result = fragment_updater.update_references(number, references, user)
    assert result == (injected_fragment, False)


def test_update_references_invalid(
    fragment_updater, bibliography, user, fragment_repository, when
):
    fragment = FragmentFactory.build()
    number = fragment.number
    reference = ReferenceFactory.build()
    when(bibliography).find(reference.id).thenRaise(NotFoundError)
    (when(fragment_repository).query_by_museum_number(number).thenReturn(fragment))
    references = (reference,)

    with pytest.raises(DataError):
        fragment_updater.update_references(number, references, user)


@pytest.mark.parametrize(
    "field,value",
    [("introduction", "Test introduction"), ("notes", "Test notes")],
)
def test_update_edition_metadata_field(
    field,
    value,
    fragment_updater: FragmentUpdater,
    user,
    fragment_repository,
    changelog,
    when,
):
    fragment: Fragment = FragmentFactory.build()
    number = fragment.number
    updated_fragment = getattr(fragment, f"set_{field}")(value)
    when(fragment_repository).query_by_museum_number(number).thenReturn(fragment)
    expect_changelog(when, changelog, user, number, fragment, updated_fragment)
    when(fragment_repository).update_field(field, updated_fragment).thenReturn()

    result = fragment_updater.update_edition(number, user, **{field: value})
    assert result == (updated_fragment, False)


@freeze_time(FROZEN_TIME)
def test_update_lemma_annotation(
    fragment_updater, user, fragment_repository, parallel_line_injector, changelog, when
):
    transliterated_fragment = TransliteratedFragmentFactory.build()
    number = transliterated_fragment.number

    annotation = {1: {3: ["aklu I"]}}
    lemmatized_fragment = transliterated_fragment.update_lemma_annotation(annotation)

    (
        when(fragment_repository)
        .query_by_museum_number(number)
        .thenReturn(transliterated_fragment)
    )
    injected_fragment = lemmatized_fragment.set_text(
        parallel_line_injector.inject_transliteration(lemmatized_fragment.text)
    )
    expect_changelog(
        when, changelog, user, number, transliterated_fragment, lemmatized_fragment
    )
    when(fragment_repository).update_field(
        "lemmatization", lemmatized_fragment
    ).thenReturn()

    result = fragment_updater.update_lemma_annotation(number, annotation, user)
    assert result == (injected_fragment, False)


@freeze_time(FROZEN_TIME)
def test_update_named_entities(
    fragment_updater,
    named_entity_spans,
    user,
    fragment_repository,
    parallel_line_injector,
    changelog,
    when,
):
    transliterated_fragment: Fragment = TransliteratedFragmentFactory.build()
    number = transliterated_fragment.number

    annotated_fragment = transliterated_fragment.set_named_entities(named_entity_spans)

    (
        when(fragment_repository)
        .query_by_museum_number(number)
        .thenReturn(transliterated_fragment)
    )
    injected_fragment = annotated_fragment.set_text(
        parallel_line_injector.inject_transliteration(annotated_fragment.text)
    )
    expect_changelog(
        when, changelog, user, number, transliterated_fragment, annotated_fragment
    )
    when(fragment_repository).update_field(
        "named_entities", annotated_fragment
    ).thenReturn()

    result = fragment_updater.update_named_entities(
        number, named_entity_spans, [], user
    )
    assert result == (injected_fragment, False)
