import attr
import pytest

from ebl.dictionary.domain.word import WordId
from ebl.errors import NotFoundError
from ebl.fragmentarium.application.fragment_schema import FragmentSchema
from ebl.fragmentarium.domain.transliteration_query import TransliterationQuery
from ebl.fragmentarium.domain.transliteration_update import TransliterationUpdate
from ebl.tests.factories.bibliography import ReferenceFactory
from ebl.tests.factories.fragment import (
    FragmentFactory,
    LemmatizedFragmentFactory,
    TransliteratedFragmentFactory,
)
from ebl.transliteration.domain.atf import Atf, Flag
from ebl.transliteration.domain.enclosure_tokens import (
    BrokenAway,
    Erasure,
    PerhapsBrokenAway,
)
from ebl.transliteration.domain.labels import LineNumberLabel
from ebl.transliteration.domain.lemmatization import Lemmatization
from ebl.transliteration.domain.line import ControlLine, EmptyLine, TextLine
from ebl.transliteration.domain.sign_tokens import Logogram, Reading
from ebl.transliteration.domain.text import Text
from ebl.transliteration.domain.tokens import Joiner, ValueToken
from ebl.transliteration.domain.word_tokens import Word

COLLECTION = "fragments"


ANOTHER_LEMMATIZED_FRAGMENT = attr.evolve(
    TransliteratedFragmentFactory.build(),
    text=Text(
        (
            TextLine(
                "1'.",
                (
                    Word(
                        parts=[Logogram.of_name("GI", 6)],
                        unique_lemma=(WordId("ginâ I"),),
                    ),
                    Word(
                        parts=[Reading.of_name("ana")], unique_lemma=(WordId("ana II"),)
                    ),
                    Word(
                        parts=[Reading.of_name("ana")], unique_lemma=(WordId("ana II"),)
                    ),
                    Word(
                        parts=[
                            Reading.of_name("u", 4),
                            Joiner.hyphen(),
                            Reading.of_name("šu"),
                        ],
                        unique_lemma=(WordId("ūsu I"),),
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
    fragment_number = fragment_repository.create(fragment)

    assert database[COLLECTION].find_one({"_id": fragment_number}) == SCHEMA.dump(
        fragment
    )


def test_query_by_fragment_number(database, fragment_repository):
    fragment = LemmatizedFragmentFactory.build()
    database[COLLECTION].insert_one(SCHEMA.dump(fragment))

    assert fragment_repository.query_by_fragment_number(fragment.number) == fragment


def test_fragment_not_found(fragment_repository):
    with pytest.raises(NotFoundError):
        fragment_repository.query_by_fragment_number("unknown id")


def test_find_random(fragment_repository,):
    fragment = FragmentFactory.build()
    transliterated_fragment = TransliteratedFragmentFactory.build()
    for a_fragment in fragment, transliterated_fragment:
        fragment_repository.create(a_fragment)

    assert fragment_repository.query_random_by_transliterated() == [
        transliterated_fragment
    ]


def test_folio_pager_exception(fragment_repository):
    query = "1841-07-26, 57"
    with pytest.raises(NotFoundError):
        fragment_repository.query_next_and_previous_fragment(query)


FRAGMENTS = ["1841-07-26, 54", "1841-07-26, 57", "1841-07-26, 63"]


@pytest.mark.parametrize(
    "query,  existing,expected",
    [
        ("1841-07-26, 57", FRAGMENTS, ["1841-07-26, 54", "1841-07-26, 63"]),
        ("1841-07-26, 63", FRAGMENTS, ["1841-07-26, 57", "1841-07-26, 54"]),
        ("1841-07-26, 54", FRAGMENTS, ["1841-07-26, 63", "1841-07-26, 57"]),
        ("1841-07-26, 54", FRAGMENTS[:2], ["1841-07-26, 57", "1841-07-26, 57"]),
    ],
)
def test_query_next_and_previous_fragment(
    query, existing, expected, fragment_repository
):
    for fragmentNumber in existing:
        fragment_repository.create(FragmentFactory.build(number=fragmentNumber))

    results = list(fragment_repository.query_next_and_previous_fragment(query).values())
    assert results == expected


def test_query_next_and_previous_fragment_exception(fragment_repository):
    query = "1841-07-26, 57"
    with pytest.raises(NotFoundError):
        fragment_repository.query_next_and_previous_fragment(query)


def test_update_transliteration_with_record(fragment_repository, user):
    fragment = FragmentFactory.build()
    fragment_number = fragment_repository.create(fragment)
    updated_fragment = fragment.update_transliteration(
        TransliterationUpdate(Atf("$ (the transliteration)"), "notes"), user
    )

    fragment_repository.update_transliteration(updated_fragment)
    result = fragment_repository.query_by_fragment_number(fragment_number)

    assert result == updated_fragment


def test_update_update_transliteration_not_found(fragment_repository):
    transliterated_fragment = TransliteratedFragmentFactory.build()
    with pytest.raises(NotFoundError):
        fragment_repository.update_transliteration(transliterated_fragment)


def test_update_lemmatization(fragment_repository):
    transliterated_fragment = TransliteratedFragmentFactory.build()
    fragment_number = fragment_repository.create(transliterated_fragment)
    tokens = transliterated_fragment.text.lemmatization.to_list()
    tokens[1][3]["uniqueLemma"] = ["aklu I"]
    updated_fragment = transliterated_fragment.update_lemmatization(
        Lemmatization.from_list(tokens)
    )

    fragment_repository.update_lemmatization(updated_fragment)
    result = fragment_repository.query_by_fragment_number(fragment_number)

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
                                "1.",
                                (
                                    Word(parts=[Reading.of_name("first")]),
                                    Word(parts=[Reading.of_name("line")]),
                                ),
                            ),
                            ControlLine("$", (ValueToken("ignore"),)),
                            EmptyLine(),
                        )
                    )
                )
            ),
            SCHEMA.dump(
                FragmentFactory.build(
                    text=Text(
                        (
                            ControlLine("$", (ValueToken("ignore"),)),
                            TextLine("1.", (Word(parts=[Reading.of_name("second")]),)),
                            TextLine("1.", (Word(parts=[Reading.of_name("third")]),)),
                            ControlLine("$", (ValueToken("ignore"),)),
                            TextLine("1.", (Word(parts=[Reading.of_name("fourth")]),)),
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

    assert (
        fragment_repository.query_by_fragment_cdli_or_accession_number(fragment.number)
    ) == [fragment]


def test_search_finds_by_accession(database, fragment_repository):
    fragment = FragmentFactory.build()
    database[COLLECTION].insert_many(
        [SCHEMA.dump(fragment), SCHEMA.dump(FragmentFactory.build())]
    )

    assert (
        fragment_repository.query_by_fragment_cdli_or_accession_number(fragment.number)
    ) == [fragment]


def test_search_finds_by_cdli(database, fragment_repository):
    fragment = FragmentFactory.build()
    database[COLLECTION].insert_many(
        [SCHEMA.dump(fragment), SCHEMA.dump(FragmentFactory.build())]
    )

    assert (
        fragment_repository.query_by_fragment_cdli_or_accession_number(fragment.number)
    ) == [fragment]


def test_search_not_found(fragment_repository):
    assert (fragment_repository.query_by_fragment_cdli_or_accession_number("K.1")) == []


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
    transliterated_fragment = TransliteratedFragmentFactory.build()
    database[COLLECTION].insert_many(
        [SCHEMA.dump(transliterated_fragment), SCHEMA.dump(FragmentFactory.build()),]
    )

    assert fragment_repository.query_transliterated() == [transliterated_fragment]


def test_find_lemmas(fragment_repository):
    lemmatized_fragment = LemmatizedFragmentFactory.build()
    fragment_repository.create(lemmatized_fragment)
    fragment_repository.create(ANOTHER_LEMMATIZED_FRAGMENT)

    assert fragment_repository.query_lemmas("GI₆") == [["ginâ I"]]


def test_find_lemmas_multiple(fragment_repository):
    lemmatized_fragment = LemmatizedFragmentFactory.build()
    fragment_repository.create(lemmatized_fragment)
    fragment_repository.create(ANOTHER_LEMMATIZED_FRAGMENT)

    assert fragment_repository.query_lemmas("ana") == [["ana II"], ["ana I"]]


@pytest.mark.parametrize(
    "parts",
    [
        [
            BrokenAway.open(),
            PerhapsBrokenAway.open(),
            Reading.of(
                [ValueToken("a"), ValueToken("n"), ValueToken("a")],
                flags=[Flag.DAMAGE, Flag.COLLATION, Flag.UNCERTAIN, Flag.CORRECTION],
            ),
            PerhapsBrokenAway.close(),
            BrokenAway.close(),
        ],
        [Erasure.open(), Erasure.center(), Reading.of_name("ana"), Erasure.close()],
    ],
)
def test_find_lemmas_ignores_in_value(parts, fragment_repository):
    fragment = FragmentFactory.build(
        text=Text.of_iterable(
            [
                TextLine.of_iterable(
                    LineNumberLabel.from_atf("1'."),
                    [Word(parts=parts, unique_lemma=(WordId("ana I"),))],
                )
            ]
        ),
        signs="DIŠ",
    )
    fragment_repository.create(fragment)

    assert fragment_repository.query_lemmas("ana") == [["ana I"]]


@pytest.mark.parametrize(
    "query,expected",
    [
        ("[(a)]n[(a*#!?)]", [["ana I"]]),
        ("°ana\\me-e-li°", []),
        ("°me-e-li\\ana°", [["ana I"]]),
        ("°\\ana°", [["ana I"]]),
    ],
)
def test_find_lemmas_ignores_in_query(query, expected, fragment_repository):
    lemmatized_fragment = LemmatizedFragmentFactory.build()
    fragment_repository.create(lemmatized_fragment)

    assert fragment_repository.query_lemmas(query) == expected


def test_find_lemmas_not_found(fragment_repository):
    lemmatized_fragment = LemmatizedFragmentFactory.build()
    fragment_repository.create(lemmatized_fragment)
    assert fragment_repository.query_lemmas("aklu") == []


def test_update_references(fragment_repository):
    reference = ReferenceFactory.build()
    fragment = FragmentFactory.build()
    fragment_number = fragment_repository.create(fragment)
    references = (reference,)
    updated_fragment = fragment.set_references(references)

    fragment_repository.update_references(updated_fragment)
    result = fragment_repository.query_by_fragment_number(fragment_number)

    assert result == updated_fragment


def test_update_update_references(fragment_repository):
    transliterated_fragment = TransliteratedFragmentFactory.build()
    with pytest.raises(NotFoundError):
        fragment_repository.update_references(transliterated_fragment)
