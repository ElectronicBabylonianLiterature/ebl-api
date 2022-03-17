import attr
import pytest


from ebl.dictionary.domain.word import WordId
from ebl.errors import NotFoundError
from ebl.fragmentarium.application.fragment_schema import FragmentSchema
from ebl.fragmentarium.application.joins_schema import JoinSchema
from ebl.fragmentarium.application.line_to_vec import LineToVecEntry
from ebl.fragmentarium.domain.fragment import Genre
from ebl.fragmentarium.domain.museum_number import MuseumNumber
from ebl.fragmentarium.domain.transliteration_update import TransliterationUpdate
from ebl.lemmatization.domain.lemmatization import Lemmatization, LemmatizationToken
from ebl.tests.factories.bibliography import ReferenceFactory
from ebl.tests.factories.fragment import (
    FragmentFactory,
    JoinFactory,
    LemmatizedFragmentFactory,
    TransliteratedFragmentFactory,
)
from ebl.transliteration.domain.lark_parser import parse_atf_lark
from ebl.transliteration.domain.line import ControlLine, EmptyLine
from ebl.transliteration.domain.line_number import LineNumber
from ebl.transliteration.domain.normalized_akkadian import AkkadianWord
from ebl.transliteration.domain.parallel_line import ParallelFragment
from ebl.transliteration.domain.sign_tokens import Logogram, Reading
from ebl.transliteration.domain.text import Text
from ebl.transliteration.domain.text_line import TextLine
from ebl.transliteration.domain.tokens import Joiner, ValueToken
from ebl.transliteration.domain.transliteration_query import TransliterationQuery
from ebl.transliteration.domain.word_tokens import Word
from ebl.fragmentarium.domain.joins import Join, Joins

COLLECTION = "fragments"
JOINS_COLLECTION = "joins"


ANOTHER_LEMMATIZED_FRAGMENT = attr.evolve(
    TransliteratedFragmentFactory.build(),
    text=Text(
        (
            TextLine(
                LineNumber(1),
                (
                    Word.of(
                        [Logogram.of_name("GI", 6)], unique_lemma=(WordId("ginâ I"),)
                    ),
                    Word.of([Reading.of_name("ana")], unique_lemma=(WordId("ana II"),)),
                    Word.of([Reading.of_name("ana")], unique_lemma=(WordId("ana II"),)),
                    Word.of(
                        [
                            Reading.of_name("u", 4),
                            Joiner.hyphen(),
                            Reading.of_name("šu"),
                        ],
                        unique_lemma=(WordId("ūsu I"),),
                    ),
                    AkkadianWord.of(
                        [ValueToken.of("ana")], unique_lemma=(WordId("normalized I"),)
                    ),
                ),
            ),
        )
    ),
    signs="MI DIŠ DIŠ UD ŠU",
)


SCHEMA = FragmentSchema()


def test_create(database, fragment_repository):
    fragment = LemmatizedFragmentFactory.build()
    fragment_id = fragment_repository.create(fragment)

    assert fragment_id == str(fragment.number)
    assert database[COLLECTION].find_one(
        {"_id": fragment_id}, projection={"_id": False}
    ) == FragmentSchema(exclude=["joins"]).dump(fragment)


def test_create_join(database, fragment_repository):
    first_join = JoinFactory.build()
    second_join = JoinFactory.build()

    fragment_repository.create_join([[first_join], [second_join]])

    assert database[JOINS_COLLECTION].find_one({}, projection={"_id": False}) == {
        "fragments": [
            {
                **JoinSchema(exclude=["is_in_fragmentarium"]).dump(first_join),
                "group": 0,
            },
            {
                **JoinSchema(exclude=["is_in_fragmentarium"]).dump(second_join),
                "group": 1,
            },
        ]
    }


def test_query_by_museum_number(database, fragment_repository):
    fragment = LemmatizedFragmentFactory.build()
    database[COLLECTION].insert_one(FragmentSchema(exclude=["joins"]).dump(fragment))

    assert fragment_repository.query_by_museum_number(fragment.number) == fragment


def test_query_by_museum_number_joins(database, fragment_repository):
    museum_number = MuseumNumber("X", "1")
    first_join = Join(museum_number, is_in_fragmentarium=True)
    second_join = Join(MuseumNumber("X", "2"), is_in_fragmentarium=False)
    fragment = LemmatizedFragmentFactory.build(
        number=museum_number, joins=Joins(((first_join,), (second_join,)))
    )
    database[COLLECTION].insert_one(FragmentSchema(exclude=["joins"]).dump(fragment))
    database[JOINS_COLLECTION].insert_one(
        {
            "fragments": [
                {
                    **JoinSchema(exclude=["is_in_fragmentarium"]).dump(first_join),
                    "group": 0,
                },
                {
                    **JoinSchema(exclude=["is_in_fragmentarium"]).dump(second_join),
                    "group": 1,
                },
            ]
        }
    )
    assert fragment_repository.query_by_museum_number(fragment.number) == fragment


def test_query_by_museum_number_references(
    database, fragment_repository, bibliography_repository
):
    reference = ReferenceFactory.build(with_document=True)
    fragment = LemmatizedFragmentFactory.build(references=(reference,))
    database[COLLECTION].insert_one(FragmentSchema(exclude=["joins"]).dump(fragment))
    bibliography_repository.create(reference.document)
    assert fragment_repository.query_by_museum_number(fragment.number) == fragment


def test_query_by_parallel_line_exists(database, fragment_repository):
    parallel_number = MuseumNumber.of("K.1")
    fragment = FragmentFactory.build(
        text=Text(
            (ParallelFragment(False, parallel_number, True, None, LineNumber(1), True),)
        )
    )
    parallel_fragment = FragmentFactory.build(number=parallel_number)
    database[COLLECTION].insert_many(
        [
            FragmentSchema(exclude=["joins"]).dump(fragment),
            FragmentSchema(exclude=["joins"]).dump(parallel_fragment),
        ]
    )

    assert fragment_repository.query_by_museum_number(fragment.number) == fragment


def test_fragment_not_found(fragment_repository):
    with pytest.raises(NotFoundError):
        fragment_repository.query_by_museum_number(MuseumNumber("unknown", "id"))


def test_find_random(fragment_repository):
    fragment = FragmentFactory.build()
    transliterated_fragment = TransliteratedFragmentFactory.build()
    for a_fragment in fragment, transliterated_fragment:
        fragment_repository.create(a_fragment)

    assert fragment_repository.query_random_by_transliterated() == [
        transliterated_fragment
    ]


def test_folio_pager_exception(fragment_repository):
    with pytest.raises(NotFoundError):
        museum_number = MuseumNumber.of("1841-07-26.54")
        fragment_repository.query_next_and_previous_folio("test", "test", museum_number)


@pytest.mark.parametrize(
    "museum_numbers",
    [
        [
            "K.1a",
            "K.1b",
            "K.1c",
            "DT.1",
            "Rm-II.1",
            "1840.10",
            "1840.11",
            "1840.12",
            "1841.54",
            "1841.57",
            "1841.63",
            "BM.0",
            "CBS.0",
            "UM.0",
            "N.0",
            "N.1",
            "1841-57.54",
            "1841-57.57",
            "1841-57.63",
            "Asb.p",
            "Asb.q",
            "Asb.z",
            "Ashm-1878.1",
            "U.0.a",
            "U.0.b",
            "U.0.c",
            "X.0",
            "X.1",
        ]
    ],
)
def test_query_next_and_previous_fragment(museum_numbers, fragment_repository):
    for fragmentNumber in museum_numbers:
        fragment_repository.create(
            FragmentFactory.build(number=MuseumNumber.of(fragmentNumber))
        )
    for museum_number in museum_numbers:
        results = fragment_repository.query_next_and_previous_fragment(
            MuseumNumber.of(museum_number)
        )
        previous_index = (museum_numbers.index(museum_number) - 1) % len(museum_numbers)
        next_index = (museum_numbers.index(museum_number) + 1) % len(museum_numbers)
        assert results.previous == MuseumNumber.of(museum_numbers[previous_index])
        assert results.next == MuseumNumber.of(museum_numbers[next_index])


def test_update_transliteration_with_record(fragment_repository, user):
    fragment = FragmentFactory.build()
    fragment_repository.create(fragment)
    updated_fragment = fragment.update_transliteration(
        TransliterationUpdate(parse_atf_lark("$ (the transliteration)"), "notes"), user
    )

    fragment_repository.update_transliteration(updated_fragment)
    result = fragment_repository.query_by_museum_number(fragment.number)

    assert result == updated_fragment


def test_update_update_transliteration_not_found(fragment_repository):
    transliterated_fragment = TransliteratedFragmentFactory.build()
    with pytest.raises(NotFoundError):
        fragment_repository.update_transliteration(transliterated_fragment)


def test_update_genres(fragment_repository):
    fragment = FragmentFactory.build(genres=tuple())
    fragment_repository.create(fragment)
    updated_fragment = fragment.set_genres(
        (Genre(["ARCHIVAL", "Administrative"], False),)
    )
    fragment_repository.update_genres(updated_fragment)
    result = fragment_repository.query_by_museum_number(fragment.number)

    assert result == updated_fragment


def test_update_lemmatization(fragment_repository):
    transliterated_fragment = TransliteratedFragmentFactory.build()
    fragment_repository.create(transliterated_fragment)
    tokens = [list(line) for line in transliterated_fragment.text.lemmatization.tokens]
    tokens[1][3] = LemmatizationToken(tokens[1][3].value, ("aklu I",))
    lemmatization = Lemmatization(tokens)
    updated_fragment = transliterated_fragment.update_lemmatization(lemmatization)

    fragment_repository.update_lemmatization(updated_fragment)
    result = fragment_repository.query_by_museum_number(transliterated_fragment.number)

    assert result == updated_fragment


def test_update_update_lemmatization_not_found(fragment_repository):
    transliterated_fragment = TransliteratedFragmentFactory.build()
    with pytest.raises(NotFoundError):
        fragment_repository.update_lemmatization(transliterated_fragment)


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


def test_statistics_no_fragments(fragment_repository):
    assert fragment_repository.count_transliterated_fragments() == 0
    assert fragment_repository.count_lines() == 0


def test_search_finds_by_id(database, fragment_repository):
    fragment = FragmentFactory.build()
    database[COLLECTION].insert_many(
        [SCHEMA.dump(fragment), SCHEMA.dump(FragmentFactory.build())]
    )

    assert fragment_repository.query_by_fragment_cdli_or_accession_number(
        str(fragment.number)
    ) == [fragment]


def test_search_finds_by_accession(database, fragment_repository):
    fragment = FragmentFactory.build()
    database[COLLECTION].insert_many(
        [SCHEMA.dump(fragment), SCHEMA.dump(FragmentFactory.build())]
    )

    assert fragment_repository.query_by_fragment_cdli_or_accession_number(
        str(fragment.number)
    ) == [fragment]


def test_search_finds_by_cdli(database, fragment_repository):
    fragment = FragmentFactory.build()
    database[COLLECTION].insert_many(
        [SCHEMA.dump(fragment), SCHEMA.dump(FragmentFactory.build())]
    )

    assert fragment_repository.query_by_fragment_cdli_or_accession_number(
        str(fragment.number)
    ) == [fragment]


def test_search_not_found(fragment_repository):
    assert (fragment_repository.query_by_fragment_cdli_or_accession_number("K.1")) == []


def test_search_reference_id(database, fragment_repository):
    fragment = FragmentFactory.build(
        references=(ReferenceFactory.build(), ReferenceFactory.build())
    )
    database[COLLECTION].insert_one(SCHEMA.dump(fragment))
    assert (
        fragment_repository.query_by_id_and_page_in_references(
            fragment.references[0].id, None
        )
    ) == [fragment]


@pytest.mark.parametrize(
    "pages", ["163", "no. 163", "161-163", "163-161" "pl. 163", "pl. 42 no. 163"]
)
def test_search_reference_id_and_pages(pages, database, fragment_repository):
    fragment = FragmentFactory.build(
        references=(ReferenceFactory.build(pages=pages), ReferenceFactory.build())
    )
    database[COLLECTION].insert_one(SCHEMA.dump(fragment))
    assert (
        fragment_repository.query_by_id_and_page_in_references(
            fragment.references[0].id, "163"
        )
    ) == [fragment]


@pytest.mark.parametrize("pages", ["1631", "1163", "116311"])
def test_empty_result_search_reference_id_and_pages(
    pages, database, fragment_repository
):
    fragment = FragmentFactory.build(
        references=(ReferenceFactory.build(pages=pages), ReferenceFactory.build())
    )
    database[COLLECTION].insert_one(SCHEMA.dump(fragment))
    assert (
        fragment_repository.query_by_id_and_page_in_references(
            fragment.references[0].id, "163"
        )
    ) == []


SEARCH_SIGNS_DATA = [
    ([["DIŠ", "UD"]], True),
    ([["KU"]], True),
    ([["UD"]], True),
    ([["MI", "DIŠ"], ["ABZ411", "BA", "MA"]], True),
    ([["IGI", "UD"]], False),
]


@pytest.mark.parametrize("signs,is_match", SEARCH_SIGNS_DATA)
def test_search_signs(signs, is_match, fragment_repository):
    transliterated_fragment = TransliteratedFragmentFactory.build()
    fragment_repository.create(transliterated_fragment)
    fragment_repository.create(FragmentFactory.build())

    result = fragment_repository.query_by_transliteration(TransliterationQuery(signs))
    expected = [transliterated_fragment] if is_match else []
    assert result == expected


def test_find_transliterated(database, fragment_repository):
    transliterated_fragment_1 = TransliteratedFragmentFactory.build(
        number=MuseumNumber.of("X.1")
    )
    transliterated_fragment_2 = TransliteratedFragmentFactory.build(
        number=MuseumNumber.of("X.2")
    )
    database[COLLECTION].insert_many(
        [
            {
                **SCHEMA.dump(transliterated_fragment_2),
                "_id": str(transliterated_fragment_2.number),
            },
            SCHEMA.dump(FragmentFactory.build()),
            {
                **SCHEMA.dump(transliterated_fragment_1),
                "_id": str(transliterated_fragment_1.number),
            },
        ]
    )

    assert fragment_repository.query_transliterated_numbers() == [
        transliterated_fragment_1.number,
        transliterated_fragment_2.number,
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
    references = (reference,)
    updated_fragment = fragment.set_references(references)

    fragment_repository.update_references(updated_fragment)
    result = fragment_repository.query_by_museum_number(fragment.number)

    assert result == updated_fragment


def test_update_update_references(fragment_repository):
    transliterated_fragment = TransliteratedFragmentFactory.build()
    with pytest.raises(NotFoundError):
        fragment_repository.update_references(transliterated_fragment)
