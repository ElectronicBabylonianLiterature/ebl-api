import pytest

from ebl.common.domain.period import Period
from ebl.dictionary.domain.word import WordId
from ebl.common.domain.scopes import Scope
from ebl.fragmentarium.application.fragment_repository import FragmentRepository
from ebl.fragmentarium.domain.fragment import (
    Fragment,
    Genre,
    Introduction,
    Notes,
    Script,
)
from ebl.fragmentarium.domain.transliteration_update import TransliterationUpdate
from ebl.tests.factories.fragment import (
    DateFactory,
    FragmentFactory,
    TransliteratedFragmentFactory,
)
from ebl.tests.fragmentarium.fragment_repository_test_helpers import COLLECTION, SCHEMA
from ebl.transliteration.domain.atf_parsers.lark_parser import parse_atf_lark
from ebl.transliteration.domain.line import ControlLine, EmptyLine
from ebl.transliteration.domain.line_number import LineNumber
from ebl.transliteration.domain.sign_tokens import Reading
from ebl.transliteration.domain.text import Text
from ebl.transliteration.domain.text_line import TextLine
from ebl.transliteration.domain.word_tokens import Word
from ebl.errors import NotFoundError
from ebl.lemmatization.domain.lemmatization import Lemmatization, LemmatizationToken


def test_update_transliteration_with_record(fragment_repository, user):
    fragment = FragmentFactory.build()
    fragment_repository.create(fragment)
    updated_fragment = fragment.update_transliteration(
        TransliterationUpdate(parse_atf_lark("$ (the transliteration)")), user
    )

    fragment_repository.update_field("transliteration", updated_fragment)

    assert (
        fragment_repository.query_by_museum_number(fragment.number) == updated_fragment
    )


def test_update_update_transliteration_not_found(fragment_repository):
    with pytest.raises(NotFoundError):
        fragment_repository.update_field(
            "transliteration", TransliteratedFragmentFactory.build()
        )


def test_update_genres(fragment_repository):
    fragment = FragmentFactory.build(genres=())
    fragment_repository.create(fragment)
    updated_fragment = fragment.set_genres(
        (Genre(["ARCHIVAL", "Administrative"], False),)
    )
    fragment_repository.update_field("genres", updated_fragment)

    assert (
        fragment_repository.query_by_museum_number(fragment.number) == updated_fragment
    )


def test_update_scopes(fragment_repository):
    fragment = FragmentFactory.build(authorized_scopes=[])
    fragment_repository.create(fragment)
    updated_fragment = fragment.set_scopes([Scope.READ_CAIC_FRAGMENTS])
    fragment_repository.update_field("authorized_scopes", updated_fragment)

    assert (
        fragment_repository.query_by_museum_number(fragment.number) == updated_fragment
    )


def test_update_date(fragment_repository):
    fragment = FragmentFactory.build(date=None)
    fragment_repository.create(fragment)
    updated_fragment = fragment.set_date(DateFactory.build())
    fragment_repository.update_field("date", updated_fragment)

    assert (
        fragment_repository.query_by_museum_number(fragment.number) == updated_fragment
    )


def test_update_dates_in_text(fragment_repository):
    fragment = FragmentFactory.build(date=None)
    fragment_repository.create(fragment)
    updated_fragment = fragment.set_dates_in_text([DateFactory.build()])
    fragment_repository.update_field("dates_in_text", updated_fragment)

    assert (
        fragment_repository.query_by_museum_number(fragment.number) == updated_fragment
    )


def test_update_lemmatization(fragment_repository):
    transliterated_fragment = TransliteratedFragmentFactory.build()
    fragment_repository.create(transliterated_fragment)
    tokens = [list(line) for line in transliterated_fragment.text.lemmatization.tokens]
    tokens[1][3] = LemmatizationToken(tokens[1][3].value, (WordId("aklu I"),))
    updated_fragment = transliterated_fragment.update_lemmatization(
        Lemmatization(tokens)
    )

    fragment_repository.update_field("lemmatization", updated_fragment)

    assert (
        fragment_repository.query_by_museum_number(transliterated_fragment.number)
        == updated_fragment
    )


def test_update_introduction(fragment_repository: FragmentRepository):
    fragment: Fragment = FragmentFactory.build(introduction=Introduction())
    fragment_repository.create(fragment)
    updated_fragment = fragment.set_introduction("Introduction")
    fragment_repository.update_field("introduction", updated_fragment)

    assert (
        fragment_repository.query_by_museum_number(fragment.number) == updated_fragment
    )


def test_update_notes(fragment_repository: FragmentRepository):
    fragment: Fragment = FragmentFactory.build(notes=Notes())
    fragment_repository.create(fragment)
    updated_fragment = fragment.set_notes("Notes")
    fragment_repository.update_field("notes", updated_fragment)

    assert (
        fragment_repository.query_by_museum_number(fragment.number) == updated_fragment
    )


def test_update_script(fragment_repository: FragmentRepository):
    fragment: Fragment = FragmentFactory.build(script=Script(Period.NONE))
    fragment_repository.create(fragment)
    updated_fragment = fragment.set_script(Script(Period.MIDDLE_ELAMITE))
    fragment_repository.update_field("script", updated_fragment)

    assert (
        fragment_repository.query_by_museum_number(fragment.number) == updated_fragment
    )


def test_update_update_lemmatization_not_found(fragment_repository):
    with pytest.raises(NotFoundError):
        fragment_repository.update_field(
            "lemmatization", TransliteratedFragmentFactory.build()
        )


def test_statistics(database, fragment_repository):
    database[COLLECTION].insert_many(
        [
            SCHEMA.dump(
                FragmentFactory.build(
                    text=Text(
                        (
                            TextLine(
                                LineNumber(1),
                                (
                                    Word.of([Reading.of_name("first")]),
                                    Word.of([Reading.of_name("line")]),
                                ),
                            ),
                            ControlLine("#", "ignore"),
                            EmptyLine(),
                        )
                    )
                )
            ),
            SCHEMA.dump(
                FragmentFactory.build(
                    text=Text(
                        (
                            ControlLine("#", "ignore"),
                            TextLine(
                                LineNumber(1), (Word.of([Reading.of_name("second")]),)
                            ),
                            TextLine(
                                LineNumber(2), (Word.of([Reading.of_name("third")]),)
                            ),
                            ControlLine("#", "ignore"),
                            TextLine(
                                LineNumber(3), (Word.of([Reading.of_name("fourth")]),)
                            ),
                        )
                    )
                )
            ),
            SCHEMA.dump(FragmentFactory.build(text=Text())),
        ]
    )

    assert fragment_repository.count_transliterated_fragments() == 2
    assert fragment_repository.count_lines() == 4
    assert fragment_repository.count_total_fragments() == 3


def test_statistics_no_fragments(fragment_repository):
    assert fragment_repository.count_transliterated_fragments() == 0
    assert fragment_repository.count_lines() == 0
    assert fragment_repository.count_total_fragments() == 0
