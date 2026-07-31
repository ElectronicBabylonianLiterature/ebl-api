from dataclasses import dataclass

from freezegun import freeze_time
import pytest

from ebl.errors import NotFoundError
from ebl.fragmentarium.application.fragment_updater import FragmentUpdater
from ebl.fragmentarium.application.fragment_schema import FragmentSchema
from ebl.fragmentarium.domain.fragment import Fragment
from ebl.lemmatization.domain.lemmatization import Lemmatization, LemmatizationToken
from ebl.tests.factories.fragment import TransliteratedFragmentFactory
from ebl.users.domain.user import User

SCHEMA = FragmentSchema()
FROZEN_TIME = "2018-09-07 15:41:24.032"


@dataclass(frozen=True)
class FragmentAnnotationContext:
    fragment_updater: FragmentUpdater
    user: User
    fragment_repository: object
    parallel_line_injector: object
    changelog: object
    when: object


@pytest.fixture
def fragment_annotation_context(request: pytest.FixtureRequest):
    return FragmentAnnotationContext(
        request.getfixturevalue("fragment_updater"),
        request.getfixturevalue("user"),
        request.getfixturevalue("fragment_repository"),
        request.getfixturevalue("parallel_line_injector"),
        request.getfixturevalue("changelog"),
        request.getfixturevalue("when"),
    )


@freeze_time(FROZEN_TIME)
def test_update_lemmatization(fragment_annotation_context):
    context = fragment_annotation_context
    transliterated_fragment = TransliteratedFragmentFactory.build()
    number = transliterated_fragment.number
    tokens = [list(line) for line in transliterated_fragment.text.lemmatization.tokens]
    tokens[1][3] = LemmatizationToken(tokens[1][3].value, ("aklu I",))
    lemmatization = Lemmatization(tokens)
    lemmatized_fragment = transliterated_fragment.update_lemmatization(lemmatization)
    (
        context.when(context.fragment_repository)
        .query_by_museum_number(number)
        .thenReturn(transliterated_fragment)
    )
    injected_fragment = lemmatized_fragment.set_text(
        context.parallel_line_injector.inject_transliteration(lemmatized_fragment.text)
    )
    context.when(context.changelog).create(
        "fragments",
        context.user.profile,
        {"_id": str(number), **SCHEMA.dump(transliterated_fragment)},
        {"_id": str(number), **SCHEMA.dump(lemmatized_fragment)},
    ).thenReturn()
    context.when(context.fragment_repository).update_field(
        "lemmatization", lemmatized_fragment
    ).thenReturn()

    result = context.fragment_updater.update_lemmatization(
        number, lemmatization, context.user
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


@freeze_time(FROZEN_TIME)
def test_update_lemma_annotation(fragment_annotation_context):
    context = fragment_annotation_context
    transliterated_fragment = TransliteratedFragmentFactory.build()
    number = transliterated_fragment.number

    annotation = {1: {3: ["aklu I"]}}
    lemmatized_fragment = transliterated_fragment.update_lemma_annotation(annotation)

    (
        context.when(context.fragment_repository)
        .query_by_museum_number(number)
        .thenReturn(transliterated_fragment)
    )
    injected_fragment = lemmatized_fragment.set_text(
        context.parallel_line_injector.inject_transliteration(lemmatized_fragment.text)
    )
    context.when(context.changelog).create(
        "fragments",
        context.user.profile,
        {"_id": str(number), **SCHEMA.dump(transliterated_fragment)},
        {"_id": str(number), **SCHEMA.dump(lemmatized_fragment)},
    ).thenReturn()
    context.when(context.fragment_repository).update_field(
        "lemmatization", lemmatized_fragment
    ).thenReturn()

    result = context.fragment_updater.update_lemma_annotation(
        number, annotation, context.user
    )
    assert result == (injected_fragment, False)


@freeze_time(FROZEN_TIME)
def test_update_named_entities(fragment_annotation_context, named_entity_spans):
    context = fragment_annotation_context
    transliterated_fragment: Fragment = TransliteratedFragmentFactory.build()
    number = transliterated_fragment.number

    annotated_fragment = transliterated_fragment.set_named_entities(named_entity_spans)

    (
        context.when(context.fragment_repository)
        .query_by_museum_number(number)
        .thenReturn(transliterated_fragment)
    )
    injected_fragment = annotated_fragment.set_text(
        context.parallel_line_injector.inject_transliteration(annotated_fragment.text)
    )
    context.when(context.changelog).create(
        "fragments",
        context.user.profile,
        {"_id": str(number), **SCHEMA.dump(transliterated_fragment)},
        {"_id": str(number), **SCHEMA.dump(annotated_fragment)},
    ).thenReturn()
    context.when(context.fragment_repository).update_field(
        "named_entities", annotated_fragment
    ).thenReturn()

    result = context.fragment_updater.update_named_entities(
        number, named_entity_spans, context.user
    )
    assert result == (injected_fragment, False)
