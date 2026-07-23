from ebl.common.domain.scopes import Scope
from freezegun import freeze_time
import pytest

from ebl.errors import NotFoundError
from ebl.fragmentarium.domain.fragment import Genre, NotLowestJoinError
from ebl.fragmentarium.domain.joins import Join, Joins
from ebl.transliteration.domain.museum_number import MuseumNumber
from ebl.fragmentarium.domain.transliteration_update import TransliterationUpdate
from ebl.tests.factories.fragment import (
    FragmentFactory,
    TransliteratedFragmentFactory,
    DateFactory,
)
from ebl.tests.fragmentarium.fragment_updater_test_helpers import (
    FROZEN_TIME,
    expect_changelog,
)
from ebl.transliteration.domain.atf import Atf
from ebl.transliteration.domain.atf_parsers.lark_parser import parse_atf_lark


@freeze_time(FROZEN_TIME)
@pytest.mark.parametrize(
    "number,ignore_lowest_join",
    [(MuseumNumber.of("X.1"), False), (MuseumNumber.of("X.3"), True)],
)
def test_update_edition(
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
    expect_changelog(
        when, changelog, user, number, transliterated_fragment, transliterated_fragment
    )
    (
        when(fragment_repository)
        .update_field("transliteration", transliterated_fragment)
        .thenReturn()
    )

    result = fragment_updater.update_edition(
        number,
        user,
        transliteration=transliteration,
        ignore_lowest_join=ignore_lowest_join,
    )

    assert result == (injected_fragment, False)


def test_update_update_transliteration_not_found(
    fragment_updater, user, fragment_repository, when
):
    number = "unknown.number"
    (when(fragment_repository).query_by_museum_number(number).thenRaise(NotFoundError))

    with pytest.raises(NotFoundError):
        fragment_updater.update_edition(
            number,
            user,
            transliteration=TransliterationUpdate(
                parse_atf_lark("$ (the transliteration)")
            ),
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
        fragment_updater.update_edition(
            number,
            user,
            transliteration=TransliterationUpdate(parse_atf_lark("1. x"), "X"),
            ignore_lowest_join=False,
        )


@pytest.mark.parametrize(
    "field,value",
    [
        ("genres", (Genre(["ARCHIVAL", "Administrative"], False),)),
        ("date", DateFactory.build()),
        ("dates_in_text", [DateFactory.build()]),
    ],
)
def test_update_metadata_field(
    field,
    value,
    fragment_updater,
    user,
    fragment_repository,
    parallel_line_injector,
    changelog,
    when,
):
    fragment = FragmentFactory.build()
    number = fragment.number
    updated_fragment = getattr(fragment, f"set_{field}")(value)
    injected_fragment = updated_fragment.set_text(
        parallel_line_injector.inject_transliteration(updated_fragment.text)
    )
    when(fragment_repository).query_by_museum_number(number).thenReturn(fragment)
    expect_changelog(when, changelog, user, number, fragment, updated_fragment)
    when(fragment_repository).update_field(field, updated_fragment).thenReturn()

    result = getattr(fragment_updater, f"update_{field}")(number, value, user)
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
