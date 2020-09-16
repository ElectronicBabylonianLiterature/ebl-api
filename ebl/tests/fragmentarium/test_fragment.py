import attr
import pytest  # pyre-ignore
from freezegun import freeze_time  # pyre-ignore

from ebl.fragmentarium.domain.folios import Folio, Folios
from ebl.fragmentarium.domain.fragment import (
    Fragment,
    Measure,
    UncuratedReference, Genre,
)
from ebl.fragmentarium.domain.transliteration_update import TransliterationUpdate
from ebl.tests.factories.bibliography import ReferenceFactory
from ebl.tests.factories.fragment import (
    FragmentFactory,
    LemmatizedFragmentFactory,
    TransliteratedFragmentFactory,
)
from ebl.tests.factories.record import RecordFactory
from ebl.transliteration.domain.atf import Atf
from ebl.transliteration.domain.lark_parser import parse_atf_lark
from ebl.transliteration.domain.lemmatization import (
    Lemmatization,
    LemmatizationError,
)
from ebl.transliteration.domain.text import Text
from ebl.fragmentarium.domain.museum_number import MuseumNumber


def test_number():
    number = MuseumNumber("K", "1")
    fragment = FragmentFactory.build(number=number)
    assert fragment.number == number


def test_accession():
    fragment = FragmentFactory.build(accession="accession-3")
    assert fragment.accession == "accession-3"


def test_cdli_number():
    fragment = FragmentFactory.build(cdli_number="cdli-4")
    assert fragment.cdli_number == "cdli-4"


def test_bm_id_number():
    fragment = FragmentFactory.build(bm_id_number="bmId-2")
    assert fragment.bm_id_number == "bmId-2"


def test_publication():
    fragment = FragmentFactory.build(publication="publication")
    assert fragment.publication == "publication"


def test_description():
    fragment = FragmentFactory.build(description="description")
    assert fragment.description == "description"


def test_collection():
    fragment = FragmentFactory.build(collection="Collection")
    assert fragment.collection == "Collection"


def test_script():
    fragment = FragmentFactory.build(script="NA")
    assert fragment.script == "NA"


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
    assert fragment.joins == tuple()


def test_notes():
    fragment = FragmentFactory.build()
    assert fragment.notes == ""


def test_signs():
    transliterated_fragment = TransliteratedFragmentFactory.build()
    assert transliterated_fragment.signs == TransliteratedFragmentFactory.signs


def test_record():
    record = RecordFactory.build()
    fragment = Fragment(MuseumNumber.of("X.1"), record=record)
    assert fragment.record == record


def test_folios():
    fragment = FragmentFactory.build()
    assert fragment.folios == Folios((Folio("WGL", "1"), Folio("XXX", "1")))


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
    assert fragment.references == tuple()


def test_genre():
    genres = (Genre(["ARCHIVAL", "Administrative", "Lists"], False),)
    fragment = FragmentFactory.build(genres=genres)
    assert fragment.genres == genres


def test_invalid_genre():
    with pytest.raises(ValueError):
        FragmentFactory.build(genres=(Genre(["xyz"], False),))


def test_set_genre():
    updated_genres = (Genre(["ARCHIVAL", "Administrative", "Lists"], True),)
    fragment = FragmentFactory.build(genres=tuple())
    updated_fragment = fragment.set_genres(updated_genres)
    assert updated_fragment.genres == updated_genres


def test_set_invalid_genre():
    with pytest.raises(ValueError, match="is not a valid genre"):
        Genre(["xyz", "wrq"], False)


@freeze_time("2018-09-07 15:41:24.032")
def test_add_transliteration(user):
    fragment = FragmentFactory.build()
    atf = Atf("1. x x")
    text = parse_atf_lark(atf)
    transliteration = TransliterationUpdate(text, fragment.notes)
    record = fragment.record.add_entry("", atf, user)

    updated_fragment = fragment.update_transliteration(transliteration, user)
    expected_fragment = attr.evolve(fragment, text=text, record=record)

    assert updated_fragment == expected_fragment


@freeze_time("2018-09-07 15:41:24.032")
def test_update_transliteration(user):
    lemmatized_fragment = LemmatizedFragmentFactory.build()
    lines = lemmatized_fragment.text.atf.split("\n")
    lines[1] = "2'. [...] GI₆ mu u₄-š[u ...]"
    atf = Atf("\n".join(lines))
    text = parse_atf_lark(atf)
    transliteration = TransliterationUpdate(text, "updated notes", "X X\nX")
    updated_fragment = lemmatized_fragment.update_transliteration(transliteration, user)

    expected_fragment = attr.evolve(
        lemmatized_fragment,
        text=lemmatized_fragment.text.merge(text),
        notes=transliteration.notes,
        signs=transliteration.signs,
        record=lemmatized_fragment.record.add_entry(
            lemmatized_fragment.text.atf, transliteration.text.atf, user
        ),
    )

    assert updated_fragment == expected_fragment


def test_update_notes(user):
    fragment = FragmentFactory.build()
    transliteration = TransliterationUpdate(fragment.text, "new notes")
    updated_fragment = fragment.update_transliteration(transliteration, user)

    expected_fragment = attr.evolve(fragment, notes=transliteration.notes)

    assert updated_fragment == expected_fragment


def test_update_lemmatization():
    transliterated_fragment = TransliteratedFragmentFactory.build()
    tokens = transliterated_fragment.text.lemmatization.to_list()
    tokens[1][3]["uniqueLemma"] = ["nu I"]
    lemmatization = Lemmatization.from_list(tokens)
    expected = attr.evolve(
        transliterated_fragment,
        text=transliterated_fragment.text.update_lemmatization(lemmatization),
    )

    assert transliterated_fragment.update_lemmatization(lemmatization) == expected


def test_update_lemmatization_incompatible():
    fragment = FragmentFactory.build()
    lemmatization = Lemmatization.from_list([[{"value": "mu", "uniqueLemma": []}]])
    with pytest.raises(LemmatizationError):
        fragment.update_lemmatization(lemmatization)


def test_set_references():
    fragment = FragmentFactory.build()
    references = (ReferenceFactory.build(),)
    updated_fragment = fragment.set_references(references)

    assert updated_fragment.references == references
