import falcon
import pytest

from ebl.sumerian_dictionary.domain.search_query import MAXIMUM_LIMIT
from ebl.tests.factories.sumerian_dictionary import SumerianWordFactory
from ebl.tests.sumerian_dictionary.conftest import InsertWords


SEARCH_ROUTE = "/sumerian-words"


def test_search(reader_client, insert_words: InsertWords) -> None:
    insert_words(
        SumerianWordFactory.build(id="exact", citation_form="lugal"),
        SumerianWordFactory.build(id="name", citation_form="lugala", pos="RN"),
    )

    result = reader_client.simulate_get(
        SEARCH_ROUTE, query_string="query=lugal&kind=words&source=attinger"
    )

    assert result.status == falcon.HTTP_OK
    assert result.json["total"] == 1
    assert [entry["_id"] for entry in result.json["entries"]] == ["exact"]
    assert result.json["entries"][0]["matchedAlias"] == ""
    assert "Cache-Control" not in result.headers


def test_search_without_query(reader_client) -> None:
    result = reader_client.simulate_get(SEARCH_ROUTE, query_string="")

    assert result.json == {"total": 0, "entries": []}


def test_search_pages(reader_client, insert_words: InsertWords) -> None:
    insert_words(
        *(SumerianWordFactory.build(citation_form="a" * n) for n in range(1, 6))
    )

    result = reader_client.simulate_get(
        SEARCH_ROUTE, query_string="query=a&limit=2&offset=4"
    )

    assert result.json["total"] == 5
    assert [entry["citationForm"] for entry in result.json["entries"]] == ["aaaaa"]


def test_limit_is_capped(reader_client, insert_words: InsertWords) -> None:
    insert_words(
        *(
            SumerianWordFactory.build(citation_form=f"a{n}")
            for n in range(MAXIMUM_LIMIT + 1)
        )
    )

    result = reader_client.simulate_get(SEARCH_ROUTE, query_string="query=a&limit=1000")

    assert result.json["total"] == MAXIMUM_LIMIT + 1
    assert len(result.json["entries"]) == MAXIMUM_LIMIT


def test_default_limit(reader_client, insert_words: InsertWords) -> None:
    insert_words(*(SumerianWordFactory.build(citation_form=f"a{n}") for n in range(30)))

    assert (
        len(
            reader_client.simulate_get(SEARCH_ROUTE, query_string="query=a").json[
                "entries"
            ]
        )
        == 25
    )


@pytest.mark.parametrize(
    "query_string",
    [
        "query=a&kind=nouns",
        "query=a&source=borger",
        "query=a&limit=0",
        "query=a&limit=x",
        "query=a&offset=-1",
    ],
)
def test_invalid_parameters(reader_client, query_string: str) -> None:
    assert (
        reader_client.simulate_get(SEARCH_ROUTE, query_string=query_string).status
        == falcon.HTTP_BAD_REQUEST
    )


def test_summaries_by_id(reader_client, insert_words: InsertWords) -> None:
    insert_words(*(SumerianWordFactory.build(id=id_) for id_ in ("a", "b", "c")))

    result = reader_client.simulate_get(SEARCH_ROUTE, query_string="ids=c,gone,a")

    assert result.status == falcon.HTTP_OK
    assert [summary["_id"] for summary in result.json] == ["c", "a"]


def test_repeated_ids(reader_client, insert_words: InsertWords) -> None:
    insert_words(*(SumerianWordFactory.build(id=id_) for id_ in ("a", "b", "c")))

    result = reader_client.simulate_get(SEARCH_ROUTE, query_string="ids=b&ids=c,a")

    assert [summary["_id"] for summary in result.json] == ["b", "c", "a"]


@pytest.mark.parametrize("query_string", ["ids=", "ids=,"])
def test_summaries_of_no_ids(reader_client, query_string: str) -> None:
    assert (
        reader_client.simulate_get(SEARCH_ROUTE, query_string=query_string).json == []
    )


def test_ids_cannot_be_combined_with_a_search(
    reader_client,
) -> None:
    result = reader_client.simulate_get(SEARCH_ROUTE, query_string="ids=a&query=lugal")

    assert result.status == falcon.HTTP_UNPROCESSABLE_ENTITY
