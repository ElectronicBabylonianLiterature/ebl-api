import pytest

from ebl.errors import NotFoundError
from ebl.mongo_collection import MongoCollection
from ebl.tests.mongo.sanitization_helpers import assert_no_query_details

IDENTIFIER = "client-supplied-identifier"
QUERY_FIELD_NAMES = ["citationKey", "aliases.value"]

COMPLEX_QUERIES = [
    {"$or": [{"citationKey": "abc"}, {"aliases.value": "abc"}]},
    {"citationKey": {"$in": ["abc", "def"]}},
    {"aliases.value": {"$exists": True}},
    {"deprecated": {"$ne": True}},
    {"values": {"$elemMatch": {"value": "abc", "subIndex": {"$exists": False}}}},
]


def assert_hides_query(message: str) -> None:
    assert_no_query_details(message)
    for field_name in QUERY_FIELD_NAMES:
        assert field_name not in message
    assert "abc" not in message


@pytest.fixture
def bibliography(database):
    return MongoCollection(database, "bibliography")


def test_find_one_by_id_reports_resource_and_identifier(bibliography) -> None:
    with pytest.raises(NotFoundError) as excinfo:
        bibliography.find_one_by_id(IDENTIFIER)

    assert str(excinfo.value) == f"bibliography {IDENTIFIER} not found."
    assert_hides_query(str(excinfo.value))


@pytest.mark.parametrize("query", COMPLEX_QUERIES)
def test_find_one_hides_query(bibliography, query) -> None:
    with pytest.raises(NotFoundError) as excinfo:
        bibliography.find_one(query)

    assert str(excinfo.value) == "bibliography not found."
    assert_hides_query(str(excinfo.value))


@pytest.mark.parametrize("query", COMPLEX_QUERIES)
def test_delete_one_hides_query(bibliography, query) -> None:
    with pytest.raises(NotFoundError) as excinfo:
        bibliography.delete_one(query)

    assert str(excinfo.value) == "bibliography not found."
    assert_hides_query(str(excinfo.value))


@pytest.mark.parametrize("query", COMPLEX_QUERIES)
def test_delete_many_hides_query(bibliography, query) -> None:
    with pytest.raises(NotFoundError) as excinfo:
        bibliography.delete_many(query)

    assert str(excinfo.value) == "bibliography not found."
    assert_hides_query(str(excinfo.value))


def test_update_one_by_id_reports_resource_and_identifier(bibliography) -> None:
    with pytest.raises(NotFoundError) as excinfo:
        bibliography.update_one_by_id(IDENTIFIER, {"$set": {"title": "abc"}})

    assert str(excinfo.value) == f"bibliography {IDENTIFIER} not found."
    assert_hides_query(str(excinfo.value))


@pytest.mark.parametrize("query", COMPLEX_QUERIES)
def test_update_one_hides_query(bibliography, query) -> None:
    with pytest.raises(NotFoundError) as excinfo:
        bibliography.update_one(query, {"$set": {"title": "abc"}})

    assert str(excinfo.value) == "bibliography not found."
    assert_hides_query(str(excinfo.value))


def test_replace_one_reports_resource_and_identifier(bibliography) -> None:
    with pytest.raises(NotFoundError) as excinfo:
        bibliography.replace_one({"_id": IDENTIFIER, "title": "abc"})

    assert str(excinfo.value) == f"bibliography {IDENTIFIER} not found."
    assert_hides_query(str(excinfo.value))


def test_replace_one_with_filter_reports_document_identifier(bibliography) -> None:
    with pytest.raises(NotFoundError) as excinfo:
        bibliography.replace_one(
            {"_id": IDENTIFIER, "title": "abc"},
            filter_={"citationKey": "abc"},
        )

    assert str(excinfo.value) == f"bibliography {IDENTIFIER} not found."
    assert_hides_query(str(excinfo.value))


@pytest.mark.parametrize(
    "collection_name,expected",
    [
        ("bibliography", "bibliography not found."),
        ("fragments", "fragment not found."),
        ("words", "word not found."),
        ("chapters", "chapter not found."),
        ("signs", "sign not found."),
        ("provenances", "provenance not found."),
        ("dossiers", "dossier not found."),
    ],
)
def test_resource_noun_is_singular_per_collection(
    database, collection_name, expected
) -> None:
    collection = MongoCollection(database, collection_name)

    with pytest.raises(NotFoundError) as excinfo:
        collection.find_one({"$or": [{"citationKey": "abc"}]})

    assert str(excinfo.value) == expected
