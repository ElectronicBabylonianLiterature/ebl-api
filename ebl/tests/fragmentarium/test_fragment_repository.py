from typing import Tuple, List
import attr
import pytest
import random
from ebl.common.domain.period import Period
from ebl.common.domain.scopes import Scope
from ebl.common.query.query_result import QueryItem, QueryResult

from ebl.dictionary.domain.word import WordId
from ebl.errors import NotFoundError
from ebl.fragmentarium.application.fragment_repository import FragmentRepository
from ebl.fragmentarium.infrastructure.mongo_fragment_repository import (
    MongoFragmentRepository,
)
from ebl.fragmentarium.application.fragment_schema import FragmentSchema
from ebl.fragmentarium.application.joins_schema import JoinSchema
from ebl.fragmentarium.application.line_to_vec import LineToVecEntry
from ebl.fragmentarium.domain.fragment import (
    Fragment,
    Genre,
    Introduction,
    Notes,
    Script,
)
from ebl.fragmentarium.domain.joins import Join, Joins
from ebl.fragmentarium.domain.transliteration_update import TransliterationUpdate
from ebl.common.query.query_result import LemmaQueryType
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
from ebl.transliteration.domain.museum_number import MuseumNumber
from ebl.transliteration.domain.normalized_akkadian import AkkadianWord
from ebl.transliteration.domain.parallel_line import Labels, ParallelFragment
from ebl.transliteration.domain.sign_tokens import Logogram, Reading
from ebl.transliteration.domain.text import Text
from ebl.transliteration.domain.text_line import TextLine
from ebl.transliteration.domain.tokens import Joiner, ValueToken
from ebl.transliteration.domain.transliteration_query import TransliterationQuery
from ebl.transliteration.domain.word_tokens import Word
from ebl.transliteration.application.signs_visitor import SignsVisitor
from ebl.common.query.query_schemas import QueryResultSchema
from ebl.tests.fragmentarium.test_fragments_search_route import query_item_of
from ebl.transliteration.application.sign_repository import SignRepository


COLLECTION = "fragments"
JOINS_COLLECTION = "joins"
FRAGMENT_IDS = ["K.1", "Sm.2"]
MUSEUM_NUMBERS = [
    MuseumNumber(prefix="K", number="1", suffix=""),
    MuseumNumber(prefix="Sm", number="2", suffix=""),
]


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


def create_tranliteration_query_lines(
    transliteration: str, sign_repository: SignRepository
) -> List[str]:
    return [
        TransliterationQuery(string=line, visitor=SignsVisitor(sign_repository)).regexp
        for line in transliteration.split("\n")
    ]


def test_create(database, fragment_repository):
    fragment = LemmatizedFragmentFactory.build()
    fragment_id = fragment_repository.create(fragment)

    assert fragment_id == str(fragment.number)
    assert database[COLLECTION].find_one(
        {"_id": fragment_id}, projection={"_id": False}
    ) == FragmentSchema(exclude=["joins"]).dump(fragment)


def test_create_many(database, fragment_repository):
    fragments = LemmatizedFragmentFactory.build_batch(2)
    fragment_ids = fragment_repository.create_many(fragments)

    for fragment in fragments:
        assert str(fragment.number) in fragment_ids
        assert database[COLLECTION].find_one(
            {"_id": str(fragment.number)}, projection={"_id": False}
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
            (
                ParallelFragment(
                    False, parallel_number, True, Labels(), LineNumber(1), True
                ),
            )
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
    transliterated_fragment = TransliteratedFragmentFactory.build()

    fragment_repository.create_many([FragmentFactory.build(), transliterated_fragment])

    assert fragment_repository.query_random_by_transliterated() == [
        transliterated_fragment
    ]


def test_find_random_skips_restricted_fragments(fragment_repository):
    restricted_transliterated_fragment = TransliteratedFragmentFactory.build(
        authorized_scopes=[Scope.READ_ITALIANNINEVEH_FRAGMENTS]
    )

    fragment_repository.create_many([restricted_transliterated_fragment])

    assert fragment_repository.query_random_by_transliterated() == []


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

    fragment_repository._create_sort_index()

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
        TransliterationUpdate(parse_atf_lark("$ (the transliteration)")), user
    )

    fragment_repository.update_field("transliteration", updated_fragment)
    result = fragment_repository.query_by_museum_number(fragment.number)

    assert result == updated_fragment


def test_update_update_transliteration_not_found(fragment_repository):
    transliterated_fragment = TransliteratedFragmentFactory.build()
    with pytest.raises(NotFoundError):
        fragment_repository.update_field("transliteration", transliterated_fragment)


def test_update_genres(fragment_repository):
    fragment = FragmentFactory.build(genres=tuple())
    fragment_repository.create(fragment)
    updated_fragment = fragment.set_genres(
        (Genre(["ARCHIVAL", "Administrative"], False),)
    )
    fragment_repository.update_field("genres", updated_fragment)
    result = fragment_repository.query_by_museum_number(fragment.number)

    assert result == updated_fragment


def test_update_lemmatization(fragment_repository):
    transliterated_fragment = TransliteratedFragmentFactory.build()
    fragment_repository.create(transliterated_fragment)
    tokens = [list(line) for line in transliterated_fragment.text.lemmatization.tokens]
    tokens[1][3] = LemmatizationToken(tokens[1][3].value, ("aklu I",))
    lemmatization = Lemmatization(tokens)
    updated_fragment = transliterated_fragment.update_lemmatization(lemmatization)

    fragment_repository.update_field("lemmatization", updated_fragment)
    result = fragment_repository.query_by_museum_number(transliterated_fragment.number)

    assert result == updated_fragment


def test_update_introduction(fragment_repository: FragmentRepository):
    fragment: Fragment = FragmentFactory.build(introduction=Introduction())
    fragment_repository.create(fragment)
    updated_fragment = fragment.set_introduction("Introduction")
    fragment_repository.update_field("introduction", updated_fragment)
    result = fragment_repository.query_by_museum_number(fragment.number)

    assert result == updated_fragment


def test_update_notes(fragment_repository: FragmentRepository):
    fragment: Fragment = FragmentFactory.build(notes=Notes())
    fragment_repository.create(fragment)
    updated_fragment = fragment.set_notes("Notes")
    fragment_repository.update_field("notes", updated_fragment)
    result = fragment_repository.query_by_museum_number(fragment.number)

    assert result == updated_fragment


def test_update_script(fragment_repository: FragmentRepository):
    fragment: Fragment = FragmentFactory.build(script=Script(Period.NONE))
    fragment_repository.create(fragment)
    updated_fragment = fragment.set_script(Script(Period.MIDDLE_ELAMITE))
    fragment_repository.update_field("script", updated_fragment)
    result = fragment_repository.query_by_museum_number(fragment.number)

    assert result == updated_fragment


def test_update_update_lemmatization_not_found(fragment_repository):
    transliterated_fragment = TransliteratedFragmentFactory.build()
    with pytest.raises(NotFoundError):
        fragment_repository.update_field("lemmatization", transliterated_fragment)


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


def test_query_fragmentarium_number(database, fragment_repository):
    fragment = FragmentFactory.build()
    database[COLLECTION].insert_many(
        [SCHEMA.dump(fragment), SCHEMA.dump(FragmentFactory.build())]
    )

    assert fragment_repository.query(
        {"number": str(fragment.number)}
    ) == QueryResultSchema().load(
        {
            "items": [query_item_of(fragment)],
            "matchCountTotal": 0,
        }
    )


def test_query_fragmentarium_not_found(fragment_repository):
    assert (fragment_repository.query({"number": "K.1"})) == QueryResult.create_empty()


def test_query_fragmentarium_reference_id(database, fragment_repository):
    fragment = FragmentFactory.build(references=(ReferenceFactory.build(),))
    database[COLLECTION].insert_one(SCHEMA.dump(fragment))
    assert fragment_repository.query(
        {"bibId": fragment.references[0].id}
    ) == QueryResultSchema().load(
        {
            "items": [query_item_of(fragment)],
            "matchCountTotal": 0,
        }
    )


@pytest.mark.parametrize(
    "pages", ["163", "no. 163", "161-163", "163-161" "pl. 163", "pl. 42 no. 163"]
)
def test_query_fragmentarium_id_and_pages(pages, database, fragment_repository):
    fragment = FragmentFactory.build(
        references=(ReferenceFactory.build(pages=pages), ReferenceFactory.build())
    )
    database[COLLECTION].insert_one(SCHEMA.dump(fragment))
    assert fragment_repository.query(
        {"bibId": fragment.references[0].id, "pages": "163"}
    ) == QueryResultSchema().load(
        {
            "items": [query_item_of(fragment)],
            "matchCountTotal": 0,
        }
    )


@pytest.mark.parametrize("pages", ["1631", "1163", "116311"])
def test_empty_result_query_reference_id_and_pages(
    pages, database, fragment_repository
):
    fragment = FragmentFactory.build(
        references=(ReferenceFactory.build(pages=pages), ReferenceFactory.build())
    )
    database[COLLECTION].insert_one(SCHEMA.dump(fragment))
    assert (
        fragment_repository.query({"bibId": fragment.references[0].id, "pages": "163"})
    ) == QueryResult.create_empty()


@pytest.mark.parametrize(
    "string,expected_lines",
    [
        ("DIŠ UD", [1]),
        ("KU", [0]),
        ("UD", [1, 3]),
        ("MI DIŠ\nU BA MA", [1, 2]),
        ("IGI UD", []),
    ],
)
def test_query_fragmentarium_transliteration(
    string, expected_lines, fragment_repository, sign_repository, signs
):
    for sign in signs:
        sign_repository.create(sign)
    transliterated_fragment = TransliteratedFragmentFactory.build()
    fragment_repository.create_many([transliterated_fragment, FragmentFactory.build()])

    pattern = create_tranliteration_query_lines(string, sign_repository)
    result = fragment_repository.query({"transliteration": pattern})
    expected = (
        QueryResultSchema().load(
            {
                "items": [
                    query_item_of(
                        transliterated_fragment,
                        expected_lines,
                        len(expected_lines) - (len(pattern) > 1),
                    )
                ],
                "matchCountTotal": len(expected_lines) - (len(pattern) > 1),
            }
        )
        if expected_lines
        else QueryResult.create_empty()
    )

    assert result == expected


def test_query_fragmentarium_sorting(fragment_repository, sign_repository, signs):
    for sign in signs:
        sign_repository.create(sign)

    fragments = [
        TransliteratedFragmentFactory.build(
            number=MuseumNumber.of("X.0"), script=Script(Period.FARA)
        ),
        attr.evolve(
            TransliteratedFragmentFactory.build(number=MuseumNumber.of("X.3")),
            signs=("KU\nX\nDU\nKU\nMI"),
            script=Script(Period.OLD_ASSYRIAN),
        ),
        TransliteratedFragmentFactory.build(
            number=MuseumNumber.of("X.1"), script=Script(Period.HELLENISTIC)
        ),
        TransliteratedFragmentFactory.build(
            number=MuseumNumber.of("X.2"), script=Script(Period.PROTO_ELAMITE)
        ),
    ]
    lines = [[0], [0, 3], [0], [0]]

    fragment_repository.create_many(random.sample(fragments, len(fragments)))

    result = fragment_repository.query(
        {"transliteration": create_tranliteration_query_lines("KU", sign_repository)}
    )
    assert result == QueryResultSchema().load(
        {
            "items": [
                query_item_of(fragment, lines)
                for fragment, lines in zip(fragments, lines)
            ],
            "matchCountTotal": 5,
        }
    )


def test_query_fragmentarium_transliteration_and_number(
    fragment_repository, sign_repository, signs
):
    for sign in signs:
        sign_repository.create(sign)
    transliterated_fragment = TransliteratedFragmentFactory.build()
    fragment_repository.create_many([transliterated_fragment, FragmentFactory.build()])

    result = fragment_repository.query(
        {
            "number": str(transliterated_fragment.number),
            "transliteration": create_tranliteration_query_lines(
                "DIŠ UD", sign_repository
            ),
        }
    )
    assert result == QueryResultSchema().load(
        {
            "items": [
                query_item_of(
                    transliterated_fragment,
                    [
                        1,
                    ],
                )
            ],
            "matchCountTotal": 1,
        }
    )


def test_query_fragmentarium_transliteration_and_number_and_references(
    fragment_repository, sign_repository, signs
):
    for sign in signs:
        sign_repository.create(sign)
    pages = "163"
    transliterated_fragment = TransliteratedFragmentFactory.build(
        references=(ReferenceFactory.build(pages=pages), ReferenceFactory.build())
    )

    fragment_repository.create_many([transliterated_fragment, FragmentFactory.build()])

    result = fragment_repository.query(
        {
            "number": str(transliterated_fragment.number),
            "transliteration": create_tranliteration_query_lines(
                "DIŠ UD", sign_repository
            ),
            "bibId": transliterated_fragment.references[0].id,
            "pages": pages,
        },
    )
    assert result == QueryResultSchema().load(
        {
            "items": [
                query_item_of(
                    transliterated_fragment,
                    [
                        1,
                    ],
                )
            ],
            "matchCountTotal": 1,
        }
    )


def test_query_fragmentarium_transliteration_and_number_and_references_not_found(
    fragment_repository, sign_repository, signs
):
    for sign in signs:
        sign_repository.create(sign)
    pages = "163"
    transliterated_fragment = TransliteratedFragmentFactory.build(
        references=(ReferenceFactory.build(pages=pages), ReferenceFactory.build())
    )
    fragment_repository.create_many([transliterated_fragment, FragmentFactory.build()])

    result = fragment_repository.query(
        {
            "number": str(transliterated_fragment.number),
            "transliteration": create_tranliteration_query_lines(
                "DIŠ UD", sign_repository
            ),
            "bibId": transliterated_fragment.references[0].id,
            "pages": f"{pages}123",
        },
    )
    assert result == QueryResult.create_empty()


def test_find_transliterated(database, fragment_repository):
    transliterated_fragment_1 = TransliteratedFragmentFactory.build(
        number=MuseumNumber.of("X.1")
    )
    transliterated_fragment_2 = TransliteratedFragmentFactory.build(
        number=MuseumNumber.of("X.2")
    )
    fragment_repository.create_many(
        [transliterated_fragment_1, transliterated_fragment_2]
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

    fragment_repository.update_field("references", updated_fragment)
    result = fragment_repository.query_by_museum_number(fragment.number)

    assert result == updated_fragment


def test_update_update_references(fragment_repository):
    transliterated_fragment = TransliteratedFragmentFactory.build()
    with pytest.raises(NotFoundError):
        fragment_repository.update_field("references", transliterated_fragment)


@pytest.mark.parametrize(
    "query_type,lemmas,expected",
    [
        (
            LemmaQueryType.AND,
            ("ana I",),
            QueryResult(
                [
                    QueryItem(
                        MUSEUM_NUMBERS[0],
                        (1,),
                        1,
                    ),
                ],
                1,
            ),
        ),
        (
            LemmaQueryType.OR,
            ("ana I", "kīdu I"),
            QueryResult(
                [
                    QueryItem(
                        MUSEUM_NUMBERS[0],
                        (1, 2),
                        2,
                    )
                ],
                2,
            ),
        ),
        (
            LemmaQueryType.OR,
            ("ana I", "kur II", "kīdu I"),
            QueryResult(
                [
                    QueryItem(
                        MUSEUM_NUMBERS[0],
                        (1, 2),
                        2,
                    ),
                    QueryItem(
                        MUSEUM_NUMBERS[1],
                        (0,),
                        1,
                    ),
                ],
                3,
            ),
        ),
        (
            LemmaQueryType.LINE,
            ("ana I", "kīdu I"),
            QueryResult(
                [],
                0,
            ),
        ),
        (
            LemmaQueryType.LINE,
            ("kīdu I", "u I", "bamātu I"),
            QueryResult(
                [
                    QueryItem(
                        MUSEUM_NUMBERS[0],
                        (2,),
                        1,
                    )
                ],
                1,
            ),
        ),
        (
            LemmaQueryType.AND,
            ("kur II", "uk I", "ap III"),
            QueryResult(
                [
                    QueryItem(
                        MUSEUM_NUMBERS[1],
                        (0,),
                        1,
                    )
                ],
                1,
            ),
        ),
        (
            LemmaQueryType.PHRASE,
            ("uk I", "kur II"),
            QueryResult(
                [
                    QueryItem(
                        MUSEUM_NUMBERS[1],
                        (0,),
                        1,
                    )
                ],
                1,
            ),
        ),
        (
            LemmaQueryType.PHRASE,
            ("uk I", "ap III"),
            QueryResult(
                [],
                0,
            ),
        ),
    ],
)
def test_query_lemmas(
    fragment_repository: MongoFragmentRepository,
    query_type: LemmaQueryType,
    lemmas: Tuple[str],
    expected: QueryResult,
):
    line_with_lemmas = TextLine.of_iterable(
        LineNumber(2, True),
        (
            Word.of([Reading.of_name("uk")], unique_lemma=(WordId("uk I"),)),
            Word.of([Reading.of_name("kur")], unique_lemma=(WordId("kur II"),)),
            Word.of([Reading.of_name("ap")], unique_lemma=(WordId("ap III"),)),
        ),
    )
    fragment = LemmatizedFragmentFactory.build(
        number=MUSEUM_NUMBERS[0],
        script=Script(Period.NEO_ASSYRIAN),
    )
    fragment_with_phrase = attr.evolve(
        fragment,
        number=MUSEUM_NUMBERS[1],
        text=attr.evolve(fragment.text, lines=[line_with_lemmas]),
        script=Script(Period.NEO_ASSYRIAN),
    )
    fragment_repository.create(fragment)
    fragment_repository.create(fragment_with_phrase)
    fragment_repository._create_sort_index()

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
    "key,number",
    [
        (0, 0),
        (1, 1),
        (2, 2),
        (3, 3),
        (4, 4),
        (5, 0),
        (-1, 4),
    ],
)
def test_query_by_sort_key(fragment_repository: MongoFragmentRepository, key: int, number: int):
    museum_numbers = [MuseumNumber("B", str(i)) for i in range(5)]
    fragments = [FragmentFactory.build(number=number) for number in museum_numbers]

    fragment_repository.create_many(fragments)
    fragment_repository._create_sort_index()

    assert fragment_repository.query_by_sort_key(key) == museum_numbers[number]


def test_query_by_sort_key_no_index(fragment_repository: MongoFragmentRepository):
    fragment_repository.create(FragmentFactory.build(number=MuseumNumber("B", "0")))

    with pytest.raises(NotFoundError, match="Unable to find fragment with _sortKey 0"):
        fragment_repository.query_by_sort_key(0)
