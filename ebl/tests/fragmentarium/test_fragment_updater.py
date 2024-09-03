from ebl.common.domain.scopes import Scope
from freezegun import freeze_time
import pytest

from ebl.errors import DataError, NotFoundError
from ebl.fragmentarium.application.fragment_schema import FragmentSchema
from ebl.fragmentarium.application.fragment_updater import FragmentUpdater
from ebl.fragmentarium.domain.fragment import Fragment, Genre, NotLowestJoinError
from ebl.fragmentarium.domain.joins import Join, Joins
from ebl.transliteration.domain.museum_number import MuseumNumber
from ebl.fragmentarium.domain.transliteration_update import TransliterationUpdate
from ebl.lemmatization.domain.lemmatization import Lemmatization, LemmatizationToken
from ebl.tests.factories.bibliography import ReferenceFactory
from ebl.tests.factories.fragment import (
    FragmentFactory,
    TransliteratedFragmentFactory,
    DateFactory,
)
from ebl.transliteration.domain.atf import Atf
from ebl.transliteration.domain.lark_parser import parse_atf_lark


SCHEMA = FragmentSchema()


@freeze_time("2018-09-07 15:41:24.032")
@pytest.mark.parametrize(
    "number,ignore_lowest_join",
    [(MuseumNumber.of("X.1"), False), (MuseumNumber.of("X.3"), True)],
)
def test_update_transliteration(
    number,
    ignore_lowest_join,
    fragment_updater,
    user,
    fragment_repository,
    changelog,
    parallel_line_injector,
    when,
):
    transliterated_fragment = TransliteratedFragmentFactory.build(
        number=number,
        joins=Joins([[Join(MuseumNumber.of("X.1"), is_in_fragmentarium=True)]]),
        line_to_vec=None,
    )
    number = transliterated_fragment.number
    atf = Atf("1. x x\n2. x")
    transliteration = TransliterationUpdate(parse_atf_lark(atf), "X X\nX")
    transliterated_fragment = transliterated_fragment.update_transliteration(
        transliteration, user
    )
    injected_fragment = transliterated_fragment.set_text(
        parallel_line_injector.inject_transliteration(transliterated_fragment.text)
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
        {"_id": str(number), **SCHEMA.dump(transliterated_fragment)},
    ).thenReturn()
    (
        when(fragment_repository)
        .update_field("transliteration", transliterated_fragment)
        .thenReturn()
    )

    result = fragment_updater.update_transliteration(
        number, transliteration, user, ignore_lowest_join
    )

    assert result == (injected_fragment, False)


def test_update_update_transliteration_not_found(
    fragment_updater, user, fragment_repository, when
):
    number = "unknown.number"
    (when(fragment_repository).query_by_museum_number(number).thenRaise(NotFoundError))

    with pytest.raises(NotFoundError):
        fragment_updater.update_transliteration(
            number,
            TransliterationUpdate(parse_atf_lark("$ (the transliteration)")),
            user,
        )


def test_update_update_transliteration_not_lowest_join(
    fragment_updater, user, fragment_repository, when
):
    number = MuseumNumber.of("X.2")
    transliterated_fragment = TransliteratedFragmentFactory.build(
        number=number,
        joins=Joins([[Join(MuseumNumber.of("X.1"), is_in_fragmentarium=True)]]),
    )

    (
        when(fragment_repository)
        .query_by_museum_number(number)
        .thenReturn(transliterated_fragment)
    )

    with pytest.raises(NotLowestJoinError):
        fragment_updater.update_transliteration(
            number,
            TransliterationUpdate(parse_atf_lark("1. x"), "X"),
            user,
            False,
        )


def test_update_genres(
    fragment_updater, user, fragment_repository, parallel_line_injector, changelog, when
):
    fragment = FragmentFactory.build()
    number = fragment.number
    genres = (Genre(["ARCHIVAL", "Administrative"], False),)
    updated_fragment = fragment.set_genres(genres)
    injected_fragment = updated_fragment.set_text(
        parallel_line_injector.inject_transliteration(updated_fragment.text)
    )
    when(fragment_repository).query_by_museum_number(number).thenReturn(fragment)
    when(changelog).create(
        "fragments",
        user.profile,
        {"_id": str(number), **SCHEMA.dump(fragment)},
        {"_id": str(number), **SCHEMA.dump(updated_fragment)},
    ).thenReturn()
    when(fragment_repository).update_field("genres", updated_fragment).thenReturn()

    result = fragment_updater.update_genres(number, genres, user)
    assert result == (injected_fragment, False)


def test_update_scopes(
    fragment_updater, fragment_repository, user, parallel_line_injector, when
):
    fragment = FragmentFactory.build()
    number = fragment.number
    scopes = [Scope.READ_CAIC_FRAGMENTS]
    updated_fragment = fragment.set_scopes(scopes)
    injected_fragment = updated_fragment.set_text(
        parallel_line_injector.inject_transliteration(updated_fragment.text)
    )
    when(fragment_repository).query_by_museum_number(number).thenReturn(fragment)
    when(fragment_repository).update_field(
        "authorized_scopes", updated_fragment
    ).thenReturn()
    result = fragment_updater.update_scopes(number, scopes)

    assert result == (injected_fragment, False)


def test_update_date(
    fragment_updater, user, fragment_repository, parallel_line_injector, changelog, when
):
    fragment = FragmentFactory.build()
    number = fragment.number
    date = DateFactory.build()
    updated_fragment = fragment.set_date(date)
    injected_fragment = updated_fragment.set_text(
        parallel_line_injector.inject_transliteration(updated_fragment.text)
    )
    when(fragment_repository).query_by_museum_number(number).thenReturn(fragment)
    when(changelog).create(
        "fragments",
        user.profile,
        {"_id": str(number), **SCHEMA.dump(fragment)},
        {"_id": str(number), **SCHEMA.dump(updated_fragment)},
    ).thenReturn()
    when(fragment_repository).update_field("date", updated_fragment).thenReturn()

    result = fragment_updater.update_date(number, date, user)
    assert result == (injected_fragment, False)


def test_update_dates_in_text(
    fragment_updater, user, fragment_repository, parallel_line_injector, changelog, when
):
    fragment = FragmentFactory.build()
    number = fragment.number
    dates_in_text = [DateFactory.build()]
    updated_fragment = fragment.set_dates_in_text(dates_in_text)
    injected_fragment = updated_fragment.set_text(
        parallel_line_injector.inject_transliteration(updated_fragment.text)
    )
    when(fragment_repository).query_by_museum_number(number).thenReturn(fragment)
    when(changelog).create(
        "fragments",
        user.profile,
        {"_id": str(number), **SCHEMA.dump(fragment)},
        {"_id": str(number), **SCHEMA.dump(updated_fragment)},
    ).thenReturn()
    when(fragment_repository).update_field(
        "dates_in_text", updated_fragment
    ).thenReturn()

    result = fragment_updater.update_dates_in_text(number, dates_in_text, user)
    assert result == (injected_fragment, False)


@freeze_time("2018-09-07 15:41:24.032")
def test_update_lemmatization(
    fragment_updater, user, fragment_repository, parallel_line_injector, changelog, when
):
    transliterated_fragment = TransliteratedFragmentFactory.build()
    number = transliterated_fragment.number
    tokens = [list(line) for line in transliterated_fragment.text.lemmatization.tokens]
    tokens[1][3] = LemmatizationToken(tokens[1][3].value, ("aklu I",))
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
    when(changelog).create(
        "fragments",
        user.profile,
        {"_id": str(number), **SCHEMA.dump(transliterated_fragment)},
        {"_id": str(number), **SCHEMA.dump(lemmatized_fragment)},
    ).thenReturn()
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
    when(changelog).create(
        "fragments",
        user.profile,
        {"_id": str(number), **SCHEMA.dump(fragment)},
        {"_id": str(number), **SCHEMA.dump(updated_fragment)},
    ).thenReturn()

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


def test_update_introduction(
    fragment_updater: FragmentUpdater, user, fragment_repository, changelog, when
):
    fragment: Fragment = FragmentFactory.build()
    number = fragment.number
    introduction = "Test introduction"
    updated_fragment = fragment.set_introduction(introduction)
    when(fragment_repository).query_by_museum_number(number).thenReturn(fragment)
    when(changelog).create(
        "fragments",
        user.profile,
        {"_id": str(number), **SCHEMA.dump(fragment)},
        {"_id": str(number), **SCHEMA.dump(updated_fragment)},
    ).thenReturn()
    when(fragment_repository).update_field(
        "introduction", updated_fragment
    ).thenReturn()

    result = fragment_updater.update_introduction(number, introduction, user)
    assert result == (updated_fragment, False)


def test_update_notes(
    fragment_updater: FragmentUpdater, user, fragment_repository, changelog, when
):
    fragment: Fragment = FragmentFactory.build()
    number = fragment.number
    notes = "Test notes"
    updated_fragment = fragment.set_notes(notes)
    when(fragment_repository).query_by_museum_number(number).thenReturn(fragment)
    when(changelog).create(
        "fragments",
        user.profile,
        {"_id": str(number), **SCHEMA.dump(fragment)},
        {"_id": str(number), **SCHEMA.dump(updated_fragment)},
    ).thenReturn()
    when(fragment_repository).update_field("notes", updated_fragment).thenReturn()

    result = fragment_updater.update_notes(number, notes, user)
    assert result == (updated_fragment, False)
