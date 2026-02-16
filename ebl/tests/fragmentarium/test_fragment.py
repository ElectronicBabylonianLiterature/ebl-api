import attr
from freezegun import freeze_time
import pytest
from ebl.common.domain.period import Period

from ebl.fragmentarium.domain.folios import Folio, Folios
from ebl.fragmentarium.domain.fragment import (
    Acquisition,
    Fragment,
    Genre,
    Measure,
    Notes,
    NotLowestJoinError,
    Script,
    UncuratedReference,
)
from ebl.fragmentarium.domain.fragment_external_numbers import ExternalNumbers
from ebl.fragmentarium.domain.joins import Join, Joins
from ebl.fragmentarium.domain.line_to_vec_encoding import LineToVecEncoding
from ebl.tests.factories.parallel_line import ParallelCompositionFactory
from ebl.transliteration.domain.museum_number import MuseumNumber
from ebl.fragmentarium.domain.transliteration_update import TransliterationUpdate
from ebl.lemmatization.domain.lemmatization import (
    Lemmatization,
    LemmatizationError,
    LemmatizationToken,
)
from ebl.tests.factories.bibliography import ReferenceFactory
from ebl.tests.factories.fragment import (
    FragmentFactory,
    LemmatizedFragmentFactory,
    TransliteratedFragmentFactory,
)
from ebl.tests.factories.record import RecordFactory
from ebl.transliteration.domain.atf import Atf
from ebl.transliteration.domain.atf_parsers.lark_parser import parse_atf_lark
from ebl.transliteration.domain.markup import StringPart, EmphasisPart
from ebl.transliteration.domain.text import Text
from ebl.transliteration.domain.transliteration_query import TransliterationQuery
from ebl.transliteration.application.signs_visitor import SignsVisitor


@pytest.fixture
def transliterated_fragment() -> Fragment:
    return TransliteratedFragmentFactory.build()


@pytest.fixture
def fragment_with_token_ids(transliterated_fragment):
    return transliterated_fragment.set_token_ids()


def test_number():
    number = MuseumNumber("K", "1")
    fragment = FragmentFactory.build(number=number)
    assert fragment.number == number


def test_accession():
    fragment = FragmentFactory.build(accession="accession-3")
    assert fragment.accession == "accession-3"


def cdli_images():
    fragment = FragmentFactory.build(
        cdli_images=["dl/photo/P550449.jpg", "dl/lineart/P550449_l.jpg"]
    )
    assert fragment.cdli_images == [
        "dl/photo/P550449.jpg",
        "dl/lineart/P550449_l.jpg",
    ]


def traditional_references():
    fragment = FragmentFactory.build(
        traditional_references=["CT 1, 12", "CT I, 12", "CT I 12"]
    )
    assert fragment.traditional_references == ["CT 1, 12", "CT I, 12", "CT I 12"]


def test_publication():
    fragment = FragmentFactory.build(publication="publication")
    assert fragment.publication == "publication"  # Fixed typo in assertion


def test_acquisition():
    acquisition = Acquisition(
        description="Clay tablet purchase", supplier="Antiquities Gallery", date=1925
    )
    fragment = FragmentFactory.build(acquisition=acquisition)

    assert isinstance(fragment.acquisition, Acquisition)
    assert fragment.acquisition.description == "Clay tablet purchase"
    assert fragment.acquisition.supplier == "Antiquities Gallery"
    assert fragment.acquisition.date == 1925

    fragment = FragmentFactory.build(acquisition=None)
    assert fragment.acquisition is None


def test_description():
    fragment = FragmentFactory.build(description="description")
    assert fragment.description == "description"


def test_collection():
    fragment = FragmentFactory.build(collection="Collection")
    assert fragment.collection == "Collection"


def test_script():
    script = Script(Period.PRESARGONIC)
    fragment = FragmentFactory.build(script=script)
    assert fragment.script == script


def test_museum():
    fragment = FragmentFactory.build(museum="Museum")
    assert fragment.museum == "Museum"


def test_length():
    fragment = FragmentFactory.build()
    assert fragment.length == Measure()


def test_width():
    fragment = FragmentFactory.build()
    assert fragment.width == Measure()


def test_thickness():
    fragment = FragmentFactory.build()
    assert fragment.thickness == Measure()


def test_joins():
    fragment = FragmentFactory.build()
    assert fragment.joins == Joins()


def test_notes():
    fragment = FragmentFactory.build()
    assert fragment.notes == Notes("notes", (StringPart("notes"),))


def test_signs(transliterated_fragment):
    assert transliterated_fragment.signs == TransliteratedFragmentFactory.signs


def test_record():
    record = RecordFactory.build()
    fragment = Fragment(MuseumNumber.of("X.1"), record=record)
    assert fragment.record == record


def test_folios():
    fragment = FragmentFactory.build()
    assert fragment.folios == Folios((Folio("WGL", "1"), Folio("ARG", "1")))


def test_text():
    fragment = FragmentFactory.build()
    assert fragment.text == Text()


def test_uncurated_references():
    uncurated_references = (
        UncuratedReference("7(0)"),
        UncuratedReference("CAD 51", (34, 56)),
        UncuratedReference("7(1)"),
    )
    fragment = FragmentFactory.build(uncurated_references=uncurated_references)
    assert fragment.uncurated_references == uncurated_references


def test_uncurated_references_none():
    fragment = FragmentFactory.build()
    assert fragment.uncurated_references is None


def test_references():
    reference = RecordFactory.build()
    fragment = FragmentFactory.build(references=(reference,))
    assert fragment.references == (reference,)


def test_references_default():
    fragment = FragmentFactory.build()
    assert fragment.references == ()


def test_genre():
    genres = (Genre(["ARCHIVAL", "Administrative", "Lists"], False),)
    fragment = FragmentFactory.build(genres=genres)
    assert fragment.genres == genres


def test_set_genre():
    updated_genres = (Genre(["ARCHIVAL", "Administrative", "Lists"], True),)
    fragment = FragmentFactory.build(genres=())
    updated_fragment = fragment.set_genres(updated_genres)
    assert updated_fragment.genres == updated_genres


def test_invalid_genre():
    with pytest.raises(ValueError, match="is not a valid genre"):
        Genre(["xyz", "wrq"], False)


def test_scopes():
    scopes = ["CAIC"]
    fragment = FragmentFactory.build(authorized_scopes=scopes)
    assert fragment.authorized_scopes == scopes


@pytest.mark.parametrize(
    "number",
    [
        "cdli_number",
        "bm_id_number",
        "archibab_number",
        "bdtns_number",
        "ur_online_number",
        "hilprecht_jena_number",
        "hilprecht_heidelberg_number",
    ],
)
def test_external_number(number):
    external_numbers = ExternalNumbers(**{number: "test-42"})
    fragment = FragmentFactory.build(external_numbers=external_numbers)

    assert getattr(fragment, number) == "test-42"


def test_external_numbers():
    external_numbers = ExternalNumbers(
        cdli_number="A38", bm_id_number="W_1848-0720-117"
    )
    fragment = FragmentFactory.build(external_numbers=external_numbers)
    assert fragment.external_numbers == external_numbers


@freeze_time("2018-09-07 15:41:24.032")
def test_add_transliteration(user):
    fragment = FragmentFactory.build()
    atf = Atf("1. x x")
    text = parse_atf_lark(atf)
    transliteration = TransliterationUpdate(text)
    record = fragment.record.add_entry("", atf, user)

    updated_fragment = fragment.update_transliteration(transliteration, user)
    expected_fragment = attr.evolve(
        fragment,
        text=text.set_token_ids(),
        record=record,
        line_to_vec=((LineToVecEncoding.START, LineToVecEncoding.TEXT_LINE),),
    )

    assert updated_fragment == expected_fragment


@freeze_time("2018-09-07 15:41:24.032")
def test_update_transliteration(user):
    lemmatized_fragment = LemmatizedFragmentFactory.build()
    lines = lemmatized_fragment.text.atf.split("\n")
    lines[1] = "2'. [...] GI₆ mu u₄-š[u ...]"
    atf = Atf("\n".join(lines))
    text = parse_atf_lark(atf)
    transliteration = TransliterationUpdate(text, "X X\nX")
    updated_fragment = lemmatized_fragment.update_transliteration(transliteration, user)

    expected_fragment = attr.evolve(
        lemmatized_fragment,
        text=lemmatized_fragment.text.merge(text).set_token_ids(),
        signs=transliteration.signs,
        record=lemmatized_fragment.record.add_entry(
            lemmatized_fragment.text.atf, transliteration.text.atf, user
        ),
    )

    assert updated_fragment == expected_fragment


def test_add_lowest_join_transliteration(user):
    fragment = FragmentFactory.build(
        number=MuseumNumber.of("X.2"),
        joins=Joins([[Join(MuseumNumber.of("X.1"), is_in_fragmentarium=True)]]),
    )
    atf = Atf("1. x x")
    text = parse_atf_lark(atf)
    transliteration = TransliterationUpdate(text)

    with pytest.raises(NotLowestJoinError):
        fragment.update_lowest_join_transliteration(transliteration, user)


def test_set_notes():
    text = "Some @i{notes}"
    fragment = FragmentFactory.build()
    updated_fragment = fragment.set_notes(text)

    assert updated_fragment.notes == Notes(
        text, (StringPart("Some "), EmphasisPart("notes"))
    )


def test_update_lemmatization(transliterated_fragment):
    tokens = [list(line) for line in transliterated_fragment.text.lemmatization.tokens]
    tokens[1][3] = LemmatizationToken(tokens[1][3].value, ("nu I",))
    lemmatization = Lemmatization(tokens)
    expected = attr.evolve(
        transliterated_fragment,
        text=transliterated_fragment.text.update_lemmatization(lemmatization),
    )

    assert transliterated_fragment.update_lemmatization(lemmatization) == expected


def test_update_lemmatization_incompatible():
    fragment = FragmentFactory.build()
    lemmatization = Lemmatization(((LemmatizationToken("mu", ()),),))
    with pytest.raises(LemmatizationError):
        fragment.update_lemmatization(lemmatization)


def test_set_references():
    fragment = FragmentFactory.build()
    references = (ReferenceFactory.build(),)
    updated_fragment = fragment.set_references(references)

    assert updated_fragment.references == references


def test_set_text():
    fragment = FragmentFactory.build()
    text = Text((ParallelCompositionFactory.build(),))
    updated_fragment = fragment.set_text(text)

    assert updated_fragment.text == text


GET_MATCHING_LINES_DATA = [
    ("KU NU", "1'. [...-ku]-nu-ši [...]"),
    ("U BA MA", "3'. [... k]i-du u ba-ma-t[a ...]"),
    ("GI₆", "2'. [...] GI₆ ana GI₆ u₄-m[a ...]"),
    (
        "GI₆ DIŠ\nU BA MA",
        "2'. [...] GI₆ ana GI₆ u₄-m[a ...]\n3'. [... k]i-du u ba-ma-t[a ...]",
    ),
    (
        "NU IGI\nGI₆ DIŠ",
        "1'. [...-ku]-nu-ši [...]\n2'. [...] GI₆ ana GI₆ u₄-m[a ...]",
    ),
    (
        "MA",
        """2'. [...] GI₆ ana GI₆ u₄-m[a ...]
3'. [... k]i-du u ba-ma-t[a ...]\n6'. [...] x mu ta-ma-tu₂""",
    ),
    (
        "MA\nTA",
        "2'. [...] GI₆ ana GI₆ u₄-m[a ...]\n3'. [... k]i-du u ba-ma-t[a ...]",
    ),
    ("BU", "7'. šu/gid"),
]


@pytest.mark.parametrize("string,expected", GET_MATCHING_LINES_DATA)
def test_get_matching_lines(string, expected, sign_repository, signs):
    for sign in signs:
        sign_repository.create(sign)
    transliterated_fragment: Fragment = FragmentFactory.build(
        text=parse_atf_lark(
            Atf(
                "1'. [...-ku]-nu-ši [...]\n"
                "\n"
                "@obverse\n"
                "2'. [...] GI₆ ana GI₆ u₄-m[a ...]\n"
                "3'. [... k]i-du u ba-ma-t[a ...]\n"
                "6'. [...] x mu ta-ma-tu₂\n"
                "7'. šu/gid"
            )
        ),
        signs="KU ABZ075 ABZ207a\\u002F207b\\u0020X\n"
        "MI DIŠ MI UD MA\n"
        "KI DU ABZ411 BA MA TA\n"
        "X MU TA MA UD\n"
        "ŠU/BU",
    )

    query = TransliterationQuery(string=string, visitor=SignsVisitor(sign_repository))
    matching_text = transliterated_fragment.get_matching_lines(query)
    assert matching_text == parse_atf_lark(expected)


def test_updating_fragment_sets_token_ids(transliterated_fragment, user):
    assert {word.id_ for word in transliterated_fragment.words} == {None}

    updated_fragment = transliterated_fragment.update_transliteration(
        TransliterationUpdate(transliterated_fragment.text), user
    )
    words = updated_fragment.words

    assert [word.id_ for word in words] == [f"Word-{i + 1}" for i in range(len(words))]


def test_deleting_words_keeps_remaining_ids(transliterated_fragment, user):
    transliterated_fragment = transliterated_fragment.update_transliteration(
        TransliterationUpdate(transliterated_fragment.text), user
    )

    lines = transliterated_fragment.text.atf.split("\n")
    truncated_text = parse_atf_lark(Atf("\n".join(lines[2:])))
    transliteration = TransliterationUpdate(truncated_text)

    truncated_fragment = transliterated_fragment.update_transliteration(
        transliteration, user
    )
    expected_ids = [f"Word-{i}" for i in range(11, 22)]
    assert [word.id_ for word in truncated_fragment.words] == expected_ids


def test_get_word_by_id(fragment_with_token_ids):
    assert (
        fragment_with_token_ids.get_word_by_id("Word-1")
        == fragment_with_token_ids.words[0]
    )


def test_get_non_existent_word_by_id(fragment_with_token_ids):
    invalid_id = "foobar"
    with pytest.raises(
        ValueError, match=f"Word with id {invalid_id} not found in fragment."
    ):
        fragment_with_token_ids.get_word_by_id(invalid_id)


@pytest.fixture
def short_fragment(transliterated_fragment, user) -> Fragment:
    atf = "1'. [...-ku]-nu-ši [...]\n3'. [...] GI₆ ana"
    return transliterated_fragment.update_transliteration(
        TransliterationUpdate(parse_atf_lark(Atf(atf))), user
    )


def test_set_token_ids(transliterated_fragment):
    word_ids = [word.id_ for word in transliterated_fragment.set_token_ids().words]
    expected = [f"Word-{i + 1}" for i in range(len(word_ids))]
    assert word_ids == expected


def test_adding_words_sets_ids(short_fragment, user):
    lines = short_fragment.text.atf.split("\n")
    lines.insert(1, "2'. kur")
    transliteration = TransliterationUpdate(parse_atf_lark(Atf("\n".join(lines))))
    words = short_fragment.update_transliteration(transliteration, user).words
    expected_ids = [f"Word-{i}" for i in [1, 2, 6, 3, 4, 5]]

    assert [word.id_ for word in words] == expected_ids
