import json

import pydash
from falcon import testing

PARTNER_ALIAS = {
    "value": "dossin1967archives",
    "normalizedValue": "dossin1967archives",
    "type": "partner_id",
    "source": "partner_request",
    "status": "redirect",
}
CITATION_KEY = "dossin1967La"
CORRECTED_TITLE = "Corrected title"
RESERVATIONS = "bibliography_lookup_reservations"


def metadata_only_payload(entry: dict) -> dict:
    return pydash.omit(
        {**entry, "title": CORRECTED_TITLE},
        "aliases",
        "citationKey",
        "deprecated",
        "redirectTo",
    )


def post_entry(client, entry: dict) -> testing.Result:
    return client.simulate_post(f"/bibliography/{entry['id']}", body=json.dumps(entry))


def reservations(database) -> dict:
    return {document["_id"]: document for document in database[RESERVATIONS].find({})}
