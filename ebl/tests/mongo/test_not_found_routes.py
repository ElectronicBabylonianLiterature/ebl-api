import json

import falcon
import pytest

BIBLIOGRAPHY_ENTRY = {
    "id": "clientChosenKey",
    "type": "article-journal",
    "title": "Title",
    "issued": {"date-parts": [[2020]]},
    "author": [{"family": "Family", "given": "Given"}],
}


def assert_sanitized(result, expected_description: str) -> None:
    assert result.status == falcon.HTTP_NOT_FOUND
    assert set(result.json) == {"title", "description"}
    assert result.json["title"] == "404 Not Found"
    assert result.json["description"] == expected_description
    assert "{" not in result.json["description"]
    assert "$" not in result.json["description"]
    assert "_id" not in result.json["description"]


def test_bibliography_update_of_missing_entry(client) -> None:
    result = client.simulate_post(
        "/bibliography/clientChosenKey",
        body=json.dumps(BIBLIOGRAPHY_ENTRY),
        headers={"Content-Type": "application/json"},
    )

    assert_sanitized(result, "bibliography clientChosenKey not found.")


def test_bibliography_get_of_missing_entry_keeps_domain_message(client) -> None:
    result = client.simulate_get("/bibliography/clientChosenKey")

    assert_sanitized(result, "bibliography clientChosenKey not found.")


@pytest.mark.parametrize(
    "url,expected",
    [
        ("/words/missing-word", "word missing-word not found."),
        ("/signs/MISSING", "sign MISSING not found."),
        ("/provenances/MISSING", "provenance MISSING not found."),
    ],
)
def test_routes_report_resource_and_identifier(client, url, expected) -> None:
    assert_sanitized(client.simulate_get(url), expected)


def test_fragment_route_keeps_domain_message(client) -> None:
    assert_sanitized(
        client.simulate_get("/fragments/X.999"), "Fragment X.999 not found."
    )
