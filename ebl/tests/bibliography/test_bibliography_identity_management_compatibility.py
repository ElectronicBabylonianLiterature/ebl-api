import json

import falcon
import pytest

from ebl.tests.bibliography.bibliography_route_test_helpers import client_with_scope
from ebl.tests.bibliography.identity_management_test_helpers import (
    admin_client,
    alias,
    entry,
    manage_identity,
    stored,
)
from ebl.tests.bibliography.identity_preservation_test_helpers import (
    CORRECTED_TITLE,
    metadata_only_payload,
    post_entry,
)


@pytest.fixture
def writer_client(context):
    return client_with_scope(context, "write:bibliography")


@pytest.fixture
def subject(bibliography, user, database):
    created = entry(
        bibliography,
        user,
        "Q30000120",
        citationKey="compat1999Key",
        aliases=[alias("compat-alias")],
    )
    return created


def test_metadata_update_still_cannot_mutate_identity(writer_client, database, subject):
    result = post_entry(writer_client, {**subject, "citationKey": "hijacked1999Key"})

    assert result.status == falcon.HTTP_CONFLICT
    assert stored(database, "Q30000120")["citationKey"] == "compat1999Key"


def test_metadata_update_still_preserves_identity(writer_client, database, subject):
    result = post_entry(writer_client, metadata_only_payload(subject))

    assert result.status == falcon.HTTP_NO_CONTENT
    stored_entry = stored(database, "Q30000120")
    assert stored_entry["title"] == CORRECTED_TITLE
    assert stored_entry["citationKey"] == "compat1999Key"
    assert stored_entry["aliases"] == [alias("compat-alias")]


def test_identity_change_preserves_csl_metadata(context, database, subject):
    manage_identity(
        admin_client(context), "Q30000120", {"addAliases": [alias("extra-alias")]}
    )

    stored_entry = stored(database, "Q30000120")
    assert stored_entry["title"] == subject["title"]
    assert stored_entry["DOI"] == subject["DOI"]
    assert stored_entry["author"] == subject["author"]


def test_alias_resolution_is_unchanged(context, bibliography, subject):
    manage_identity(
        admin_client(context), "Q30000120", {"addAliases": [alias("second-alias")]}
    )

    assert bibliography.find("compat-alias")["id"] == "Q30000120"
    assert bibliography.find("second-alias")["id"] == "Q30000120"
    assert bibliography.find("compat1999Key")["id"] == "Q30000120"


def test_deprecated_resolution_is_unchanged(context, bibliography, user, subject):
    entry(bibliography, user, "Q30000121")
    manage_identity(admin_client(context), "Q30000121", {"deprecateTo": "Q30000120"})

    assert bibliography.find("Q30000121")["id"] == "Q30000120"
    assert bibliography.find_many(["Q30000121"])[0]["id"] == "Q30000120"


def test_partner_update_route_behaviour_is_unchanged(context, database, subject):
    client = client_with_scope(context, "write:bibliography export:bibliography")

    result = client.simulate_post(
        "/api/v1/bibliography/Q30000120",
        body=json.dumps({"type": "article-journal", "title": "Partner title"}),
    )

    assert result.status == falcon.HTTP_NO_CONTENT
    stored_entry = stored(database, "Q30000120")
    assert stored_entry["citationKey"] == "compat1999Key"
    assert stored_entry["aliases"] == [alias("compat-alias")]


def test_partner_route_still_rejects_server_owned_fields(context, database, subject):
    client = client_with_scope(context, "write:bibliography export:bibliography")

    result = client.simulate_post(
        "/api/v1/bibliography/Q30000120",
        body=json.dumps(
            {
                "type": "article-journal",
                "title": "Partner title",
                "aliases": [alias("partner-injected")],
            }
        ),
    )

    assert result.status == falcon.HTTP_UNPROCESSABLE_ENTITY
    assert stored(database, "Q30000120")["aliases"] == [alias("compat-alias")]


def test_identity_route_is_not_exposed_under_the_partner_prefix(context, subject):
    client = client_with_scope(context, "admin:bibliography export:bibliography")

    result = client.simulate_post(
        "/api/v1/bibliography/Q30000120/identity",
        body=json.dumps({"addAliases": [alias("partner-path")]}),
    )

    assert result.status == falcon.HTTP_NOT_FOUND
