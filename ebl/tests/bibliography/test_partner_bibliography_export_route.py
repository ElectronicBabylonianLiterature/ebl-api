import falcon

from ebl.tests.factories.bibliography import BibliographyEntryFactory


def test_partner_bibliography_export_page(client, saved_entries):
    first_page = client.simulate_get("/api/v1/bibliography", params={"limit": 2})

    assert first_page.status == falcon.HTTP_OK
    assert first_page.json["limit"] == 2
    assert [item["id"] for item in first_page.json["items"]] == [
        saved_entries[0]["id"],
        saved_entries[1]["id"],
    ]
    assert first_page.json["items"][0]["citationKey"] is None
    assert first_page.json["items"][0]["bibliographyEntry"] == saved_entries[0]
    assert first_page.json["nextCursor"] == saved_entries[1]["id"]

    second_page = client.simulate_get(
        "/api/v1/bibliography",
        params={"limit": 2, "cursor": first_page.json["nextCursor"]},
    )

    assert [item["id"] for item in second_page.json["items"]] == [
        saved_entries[2]["id"],
        saved_entries[3]["id"],
    ]


def test_partner_bibliography_export_excludes_deprecated_records(
    client, bibliography, user
):
    canonical_entry = BibliographyEntryFactory.build(id="Q30000000")
    deprecated_entry = BibliographyEntryFactory.build(
        id="Q30000001", deprecated=True, redirectTo=canonical_entry["id"]
    )
    active_entry = BibliographyEntryFactory.build(id="Q30000002")
    for entry in (canonical_entry, deprecated_entry, active_entry):
        bibliography.create(entry, user)

    first_page = client.simulate_get("/api/v1/bibliography", params={"limit": 1})
    second_page = client.simulate_get(
        "/api/v1/bibliography",
        params={"limit": 1, "cursor": first_page.json["nextCursor"]},
    )

    assert [item["id"] for item in first_page.json["items"]] == [canonical_entry["id"]]
    assert first_page.json["nextCursor"] == canonical_entry["id"]
    assert [item["id"] for item in second_page.json["items"]] == [active_entry["id"]]
    assert second_page.json["nextCursor"] is None


def test_partner_bibliography_export_caps_limit(client, saved_entries):
    result = client.simulate_get("/api/v1/bibliography", params={"limit": 999})

    assert result.status == falcon.HTTP_OK
    assert result.json["limit"] == 100


def test_partner_bibliography_entry_by_id(client, saved_entry):
    result = client.simulate_get(f"/api/v1/bibliography/{saved_entry['id']}")

    assert result.status == falcon.HTTP_OK
    assert result.json["id"] == saved_entry["id"]
    assert result.json["citationKey"] is None
    assert result.json["bibliographyEntry"] == saved_entry


def test_partner_bibliography_entry_by_deprecated_id_redirects(
    client, bibliography, user
):
    canonical_entry = BibliographyEntryFactory.build(id="CANONICAL_ID")
    deprecated_entry = BibliographyEntryFactory.build(
        id="DUPLICATE_ID", deprecated=True, redirectTo=canonical_entry["id"]
    )
    bibliography.create(canonical_entry, user)
    bibliography.create(deprecated_entry, user)

    result = client.simulate_get(f"/api/v1/bibliography/{deprecated_entry['id']}")

    assert result.status == falcon.HTTP_OK
    assert result.json["id"] == canonical_entry["id"]
    assert result.json["bibliographyEntry"] == canonical_entry


def test_partner_bibliography_entry_by_citation_key(client, bibliography, user):
    bibliography_entry = BibliographyEntryFactory.build(citationKey="miccadei2002")
    bibliography.create(bibliography_entry, user)

    result = client.simulate_get(
        f"/api/v1/bibliography/{bibliography_entry['citationKey']}"
    )

    assert result.status == falcon.HTTP_OK
    assert result.json["id"] == bibliography_entry["id"]
    assert result.json["citationKey"] == bibliography_entry["citationKey"]
    assert result.json["bibliographyEntry"] == bibliography_entry


def test_partner_bibliography_entry_by_alias(client, bibliography, user):
    alias = "legacy-id"
    bibliography_entry = BibliographyEntryFactory.build(
        aliases=[{"value": alias, "normalizedValue": alias}]
    )
    bibliography.create(bibliography_entry, user)

    result = client.simulate_get(f"/api/v1/bibliography/{alias}")

    assert result.status == falcon.HTTP_OK
    assert result.json["id"] == bibliography_entry["id"]
    assert result.json["bibliographyEntry"] == bibliography_entry


def test_partner_bibliography_entry_not_found(client):
    result = client.simulate_get("/api/v1/bibliography/not-found")

    assert result.status == falcon.HTTP_NOT_FOUND


def test_partner_bibliography_export_requires_export_scope(guest_client):
    result = guest_client.simulate_get("/api/v1/bibliography")

    assert result.status == falcon.HTTP_FORBIDDEN
