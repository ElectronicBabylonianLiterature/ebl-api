import falcon

from ebl.tests.factories.bibliography import BibliographyEntryFactory


def test_list_all_bibliography(client, saved_entry):
    result = client.simulate_get("/bibliography/all")

    assert result.json == [saved_entry["id"]]
    assert result.status == falcon.HTTP_OK


def test_list_all_bibliography_excludes_deprecated(client, bibliography, user):
    canonical_entry = BibliographyEntryFactory.build(id="CANONICAL_ID")
    deprecated_entry = BibliographyEntryFactory.build(
        id="DUPLICATE_ID", deprecated=True, redirectTo=canonical_entry["id"]
    )
    bibliography.create(canonical_entry, user)
    bibliography.create(deprecated_entry, user)

    result = client.simulate_get("/bibliography/all")

    assert result.status == falcon.HTTP_OK
    assert result.json == [canonical_entry["id"]]


def test_list_bibliography(client, saved_entries):
    ids = [entry["id"] for entry in saved_entries]
    result = client.simulate_get(f"/bibliography/list?ids={','.join(ids)}")

    assert result.json == saved_entries
    assert result.status == falcon.HTTP_OK


def test_list_bibliography_resolves_deprecated_ids(client, bibliography, user):
    canonical_entry = BibliographyEntryFactory.build(id="CANONICAL_ID")
    deprecated_entry = BibliographyEntryFactory.build(
        id="DUPLICATE_ID", deprecated=True, redirectTo=canonical_entry["id"]
    )
    bibliography.create(canonical_entry, user)
    bibliography.create(deprecated_entry, user)

    result = client.simulate_get(
        "/bibliography/list", params={"ids": deprecated_entry["id"]}
    )

    assert result.status == falcon.HTTP_OK
    assert result.json == [canonical_entry]


def test_list_bibliography_deduplicates_redirected_canonical_entries(
    client, bibliography, user
):
    canonical_entry = BibliographyEntryFactory.build(id="CANONICAL_ID")
    deprecated_entry = BibliographyEntryFactory.build(
        id="DUPLICATE_ID", deprecated=True, redirectTo=canonical_entry["id"]
    )
    bibliography.create(canonical_entry, user)
    bibliography.create(deprecated_entry, user)

    result = client.simulate_get(
        "/bibliography/list",
        params={"ids": f"{deprecated_entry['id']},{canonical_entry['id']}"},
    )

    assert result.status == falcon.HTTP_OK
    assert result.json == [canonical_entry]


def test_list_bibliography_skips_an_entry_with_a_broken_redirect(
    client, database, bibliography, user
):
    valid_entry = BibliographyEntryFactory.build(id="VALID_ID")
    bibliography.create(valid_entry, user)
    for loop_id, target in (("LOOP_A", "LOOP_B"), ("LOOP_B", "LOOP_A")):
        bibliography.create(BibliographyEntryFactory.build(id=loop_id), user)
        database["bibliography"].update_one(
            {"_id": loop_id},
            {"$set": {"deprecated": True, "redirectTo": target}},
        )

    result = client.simulate_get(
        "/bibliography/list", params={"ids": f"LOOP_A,{valid_entry['id']}"}
    )

    assert result.status == falcon.HTTP_OK
    assert result.json == [valid_entry]


def test_list_bibliography_serves_the_cached_response(
    cached_client, bibliography, user
):
    entry = BibliographyEntryFactory.build(id="Q30000123")
    bibliography.create(entry, user)
    url = "/bibliography/list"

    first_result = cached_client.simulate_get(url, params={"ids": entry["id"]})
    second_result = cached_client.simulate_get(url, params={"ids": entry["id"]})

    assert first_result.status == falcon.HTTP_OK
    assert second_result.json == first_result.json
