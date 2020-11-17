import pytest  # pyre-ignore
from freezegun import freeze_time  # pyre-ignore

from ebl.errors import DataError, NotFoundError
from ebl.fragmentarium.application.fragment_schema import FragmentSchema
from ebl.fragmentarium.domain.fragment import Genre
from ebl.fragmentarium.domain.transliteration_update import TransliterationUpdate
from ebl.tests.factories.bibliography import ReferenceFactory
from ebl.tests.factories.fragment import FragmentFactory, TransliteratedFragmentFactory
from ebl.transliteration.domain.atf import Atf
from ebl.transliteration.domain.lemmatization import Lemmatization, LemmatizationToken
from ebl.transliteration.domain.lark_parser import parse_atf_lark


SCHEMA = FragmentSchema()


@freeze_time("2018-09-07 15:41:24.032")
def test_update_transliteration(
    fragment_updater, user, fragment_repository, changelog, when
):
    transliterated_fragment = TransliteratedFragmentFactory.build()
    number = transliterated_fragment.number
    atf = Atf("1. x x\n2. x")
    transliteration = TransliterationUpdate(
        parse_atf_lark(atf), "updated notes", "X X\nX"
    )
    expected_fragment = transliterated_fragment.update_transliteration(
        transliteration, user
    )

    (
        when(fragment_repository)
        .query_by_museum_number(number)
        .thenReturn(transliterated_fragment)
    )
    when(changelog).create(
        "fragments",
        user.profile,
        {"_id": str(number), **SCHEMA.dump(transliterated_fragment)},
        {"_id": str(number), **SCHEMA.dump(expected_fragment)},
    ).thenReturn()
    (when(fragment_repository).update_transliteration(expected_fragment).thenReturn())

    updated_fragment = fragment_updater.update_transliteration(
        number, transliteration, user
    )
    assert updated_fragment == (expected_fragment, False)


def test_update_line_to_vec(
    fragment_updater, user, fragment_repository, changelog, when
):
    line_to_vec = [0, 1, 1, 2, 1, 2, 1]
    transliterated_fragment = TransliteratedFragmentFactory.build(line_to_vec=[])
    number = transliterated_fragment.number
    expected_fragment = transliterated_fragment.set_line_to_vec(line_to_vec)
    (
        when(fragment_repository)
        .query_by_museum_number(number)
        .thenReturn(transliterated_fragment)
    )
    when(changelog).create(
        "fragments",
        user.profile,
        {"_id": str(number), **SCHEMA.dump(transliterated_fragment)},
        {"_id": str(number), **SCHEMA.dump(expected_fragment)},
    ).thenReturn()
    (when(fragment_repository).update_line_to_vec(expected_fragment).thenReturn())
    updated_fragment = fragment_updater.update_line_to_vec(number, line_to_vec, user)
    assert updated_fragment == (expected_fragment, False)


def test_update_update_transliteration_not_found(
    fragment_updater, user, fragment_repository, when
):
    number = "unknown.number"
    (when(fragment_repository).query_by_museum_number(number).thenRaise(NotFoundError))

    with pytest.raises(NotFoundError):
        fragment_updater.update_transliteration(
            number,
            TransliterationUpdate(parse_atf_lark("$ (the transliteration)"), "notes"),
            user,
        )


def test_update_genres(fragment_updater, user, fragment_repository, changelog, when):
    fragment = FragmentFactory.build()
    number = fragment.number
    genres = (Genre(["ARCHIVAL", "Administrative"], False),)
    expected_fragment = fragment.set_genres(genres)

    (when(fragment_repository).query_by_museum_number(number).thenReturn(fragment))
    when(changelog).create(
        "fragments",
        user.profile,
        {"_id": str(number), **SCHEMA.dump(fragment)},
        {"_id": str(number), **SCHEMA.dump(expected_fragment)},
    ).thenReturn()
    (when(fragment_repository).update_genres(expected_fragment).thenReturn())

    updated_fragment = fragment_updater.update_genres(number, genres, user)
    assert updated_fragment == (expected_fragment, False)


@freeze_time("2018-09-07 15:41:24.032")
def test_update_lemmatization(
    fragment_updater, user, fragment_repository, changelog, when
):
    transliterated_fragment = TransliteratedFragmentFactory.build()
    number = transliterated_fragment.number
    tokens = [list(line) for line in transliterated_fragment.text.lemmatization.tokens]
    tokens[1][3] = LemmatizationToken(tokens[1][3].value, ("aklu I",))
    lemmatization = Lemmatization(tokens)
    expected_fragment = transliterated_fragment.update_lemmatization(lemmatization)
    (
        when(fragment_repository)
        .query_by_museum_number(number)
        .thenReturn(transliterated_fragment)
    )
    when(changelog).create(
        "fragments",
        user.profile,
        {"_id": str(number), **SCHEMA.dump(transliterated_fragment)},
        {"_id": str(number), **SCHEMA.dump(expected_fragment)},
    ).thenReturn()
    (when(fragment_repository).update_lemmatization(expected_fragment).thenReturn())

    updated_fragment = fragment_updater.update_lemmatization(
        number, lemmatization, user
    )
    assert updated_fragment == (expected_fragment, False)


def test_update_update_lemmatization_not_found(
    fragment_updater, user, fragment_repository, when
):
    number = "K.1"
    (when(fragment_repository).query_by_museum_number(number).thenRaise(NotFoundError))

    with pytest.raises(NotFoundError):
        fragment_updater.update_lemmatization(
            number, Lemmatization(((LemmatizationToken("1.", tuple()),),)), user
        )


def test_update_references(
    fragment_updater, bibliography, user, fragment_repository, changelog, when
):

    fragment = FragmentFactory.build()
    number = fragment.number
    reference = ReferenceFactory.build()
    references = (reference,)
    expected_fragment = fragment.set_references(references)
    when(bibliography).find(reference.id).thenReturn(reference)
    (when(fragment_repository).query_by_museum_number(number).thenReturn(fragment))
    when(fragment_repository).update_references(expected_fragment).thenReturn()
    when(changelog).create(
        "fragments",
        user.profile,
        {"_id": str(number), **SCHEMA.dump(fragment)},
        {"_id": str(number), **SCHEMA.dump(expected_fragment)},
    ).thenReturn()

    updated_fragment = fragment_updater.update_references(number, references, user)
    assert updated_fragment == (expected_fragment, False)


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
