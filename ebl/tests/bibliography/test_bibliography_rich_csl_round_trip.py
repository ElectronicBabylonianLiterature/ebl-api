import falcon

from ebl.tests.factories.bibliography import BibliographyEntryFactory


def test_frontend_shaped_rich_csl_create_get_and_edit_round_trip(client):
    entry = BibliographyEntryFactory.build(
        id="Q30000180",
        abstract="A detailed abstract.",
        keyword="lexical lists",
        editor=[{"given": "E.", "family": "Editor"}],
        translator=[{"given": "T.", "family": "Translator"}],
        URL="https://example.test/bibliography/Q30000180",
        **{
            "container-title": "Journal of Cuneiform Studies",
            "collection-title": "Babylonian Sources",
            "original-date": {"date-parts": [[1899]]},
        },
    )

    create_result = client.simulate_post("/bibliography", json=entry)
    fetched = client.simulate_get(f"/bibliography/{entry['id']}")
    edited = {
        **fetched.json,
        "title": "A corrected rich title",
        "abstract": "A corrected detailed abstract.",
    }
    edit_result = client.simulate_post(f"/bibliography/{entry['id']}", json=edited)
    refetched = client.simulate_get(f"/bibliography/{entry['id']}")

    assert create_result.status == falcon.HTTP_CREATED
    assert fetched.json == entry
    assert edit_result.status == falcon.HTTP_NO_CONTENT
    assert refetched.json == edited
