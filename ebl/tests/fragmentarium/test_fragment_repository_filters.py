from typing import Tuple

import attr
import pytest

from ebl.common.domain.period import Period
from ebl.common.domain.scopes import Scope
from ebl.common.query.query_result import LemmaQueryType, QueryItem, QueryResult
from ebl.dictionary.domain.word import WordId
from ebl.errors import NotFoundError
from ebl.fragmentarium.application.fragment_repository import FragmentRepository
from ebl.fragmentarium.domain.fragment import Script
from ebl.fragmentarium.infrastructure.mongo_fragment_repository import (
    MongoFragmentRepository,
)
from ebl.tests.factories.bibliography import ReferenceFactory
from ebl.tests.factories.fragment import (
    FragmentFactory,
    LemmatizedFragmentFactory,
    TransliteratedFragmentFactory,
)
from ebl.transliteration.domain.line_number import LineNumber
from ebl.transliteration.domain.museum_number import MuseumNumber
from ebl.transliteration.domain.sign_tokens import Reading
from ebl.transliteration.domain.text_line import TextLine
from ebl.transliteration.domain.word_tokens import Word
from ebl.fragmentarium.application.line_to_vec import LineToVecEntry
from ebl.tests.fragmentarium.fragment_repository_test_helpers import COLLECTION, SCHEMA


def test_find_transliterated(database, fragment_repository):
    transliterated_fragments = [
        TransliteratedFragmentFactory.build(number=MuseumNumber.of("X.1")),
        TransliteratedFragmentFactory.build(number=MuseumNumber.of("X.2")),
    ]
    fragment_repository.create_many(transliterated_fragments)

    assert fragment_repository.query_transliterated_numbers() == [
        fragment.number for fragment in transliterated_fragments
    ]


def test_find_transliterated_line_to_vec(database, fragment_repository):
    transliterated_fragment = TransliteratedFragmentFactory.build()
    database[COLLECTION].insert_many(
        [SCHEMA.dump(transliterated_fragment), SCHEMA.dump(FragmentFactory.build())]
    )

    assert fragment_repository.query_transliterated_line_to_vec() == [
        LineToVecEntry(
            transliterated_fragment.number,
            transliterated_fragment.script,
            transliterated_fragment.line_to_vec,
        )
    ]


def test_update_references(fragment_repository):
    reference = ReferenceFactory.build()
    fragment = FragmentFactory.build()
    fragment_repository.create(fragment)
    updated_fragment = fragment.set_references((reference,))

    fragment_repository.update_field("references", updated_fragment)

    assert (
        fragment_repository.query_by_museum_number(fragment.number) == updated_fragment
    )


def test_update_update_references(fragment_repository):
    with pytest.raises(NotFoundError):
        fragment_repository.update_field(
            "references", TransliteratedFragmentFactory.build()
        )


@pytest.mark.parametrize(
    "query_type,lemmas,expected",
    [
        (
            LemmaQueryType.AND,
            ("ana I",),
            QueryResult([QueryItem(MuseumNumber.of("K.1"), (1,), 1)], 1),
        ),
        (
            LemmaQueryType.OR,
            ("ana I", "kīdu I"),
            QueryResult([QueryItem(MuseumNumber.of("K.1"), (1, 2), 2)], 2),
        ),
        (
            LemmaQueryType.OR,
            ("ana I", "kur II", "kīdu I"),
            QueryResult(
                [
                    QueryItem(MuseumNumber.of("K.1"), (1, 2), 2),
                    QueryItem(MuseumNumber.of("Sm.2"), (0,), 1),
                ],
                3,
            ),
        ),
        (LemmaQueryType.LINE, ("ana I", "kīdu I"), QueryResult([], 0)),
        (
            LemmaQueryType.LINE,
            ("kīdu I", "u I", "bamātu I"),
            QueryResult([QueryItem(MuseumNumber.of("K.1"), (2,), 1)], 1),
        ),
        (
            LemmaQueryType.AND,
            ("kur II", "uk I", "ap III"),
            QueryResult([QueryItem(MuseumNumber.of("Sm.2"), (0,), 1)], 1),
        ),
        (
            LemmaQueryType.PHRASE,
            ("uk I", "kur II"),
            QueryResult([QueryItem(MuseumNumber.of("Sm.2"), (0,), 1)], 1),
        ),
        (LemmaQueryType.PHRASE, ("uk I", "ap III"), QueryResult([], 0)),
    ],
)
def test_query_lemmas(
    fragment_repository: MongoFragmentRepository,
    query_type: LemmaQueryType,
    lemmas: Tuple[str],
    expected: QueryResult,
):
    fragment = LemmatizedFragmentFactory.build(
        number=MuseumNumber.of("K.1"),
        script=Script(Period.NEO_ASSYRIAN),
    )
    fragment_with_phrase = attr.evolve(
        fragment,
        number=MuseumNumber.of("Sm.2"),
        text=attr.evolve(
            fragment.text,
            lines=[
                TextLine.of_iterable(
                    LineNumber(2, True),
                    (
                        Word.of(
                            [Reading.of_name("uk")], unique_lemma=(WordId("uk I"),)
                        ),
                        Word.of(
                            [Reading.of_name("kur")],
                            unique_lemma=(WordId("kur II"),),
                        ),
                        Word.of(
                            [Reading.of_name("ap")], unique_lemma=(WordId("ap III"),)
                        ),
                    ),
                )
            ],
        ),
        script=Script(Period.NEO_ASSYRIAN),
    )
    fragment_repository.create(fragment, sort_key=0)
    fragment_repository.create(fragment_with_phrase, sort_key=1)

    assert (
        fragment_repository.query({"lemmaOperator": query_type, "lemmas": lemmas})
        == expected
    )


def test_fetch_scopes(fragment_repository: FragmentRepository):
    fragment = FragmentFactory.build(
        authorized_scopes=[Scope.READ_URUKLBU_FRAGMENTS, Scope.READ_CAIC_FRAGMENTS]
    )
    fragment_repository.create(fragment)

    assert fragment_repository.fetch_scopes(fragment.number) == [
        Scope.READ_URUKLBU_FRAGMENTS,
        Scope.READ_CAIC_FRAGMENTS,
    ]


@pytest.mark.parametrize(
    "sort_key,expected_number",
    [(0, 0), (1, 1), (2, 2), (3, 3), (4, 4), (5, 0), (-1, 4)],
)
def test_query_by_sort_key(
    fragment_repository: MongoFragmentRepository,
    sort_key: int,
    expected_number: int,
):
    museum_numbers = [MuseumNumber("B", str(index)) for index in range(5)]

    for index, number in enumerate(museum_numbers):
        fragment_repository.create(FragmentFactory.build(number=number), sort_key=index)

    assert (
        fragment_repository.query_by_sort_key(sort_key)
        == museum_numbers[expected_number]
    )


def test_query_by_sort_key_no_index(fragment_repository):
    fragment_repository.create(FragmentFactory.build(number=MuseumNumber("B", "0")))

    with pytest.raises(NotFoundError, match="Unable to find fragment with _sortKey 0"):
        fragment_repository.query_by_sort_key(0)
