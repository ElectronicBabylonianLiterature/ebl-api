import json
from typing import Any, Optional, cast

from falcon import testing

from ebl.tests.bibliography.bibliography_route_test_helpers import client_with_scope
from ebl.tests.factories.bibliography import BibliographyEntryFactory

ADMIN_SCOPE = "admin:bibliography"
RESERVATIONS = "bibliography_lookup_reservations"
IDENTITY_ROUTE = "/bibliography/{}/identity"


def admin_client(context):
    return client_with_scope(context, ADMIN_SCOPE)


def manage_identity(client, id_: str, commands: dict) -> testing.Result:
    return client.simulate_post(IDENTITY_ROUTE.format(id_), body=json.dumps(commands))


def alias(value: str, **overrides) -> dict:
    return {"value": value, "normalizedValue": value, **overrides}


def entry(bibliography, user, id_: str, **overrides) -> dict:
    bibliography_entry = BibliographyEntryFactory.build(id=id_, **overrides)
    bibliography.create(bibliography_entry, user)
    return bibliography_entry


def body(result: testing.Result) -> dict:
    return cast(dict, result.json)


def description(result: testing.Result) -> str:
    return cast(str, body(result)["description"])


def reservation(database, value: str) -> Optional[dict]:
    return cast(Optional[dict], database[RESERVATIONS].find_one({"_id": value}))


def reservation_state(database, value: str) -> Optional[str]:
    document = reservation(database, value)
    return None if document is None else cast(str, document["state"])


def stored(database, id_: str) -> dict:
    return cast(dict, database["bibliography"].find_one({"_id": id_}))


def changelog_entries(database, id_: str) -> list[Any]:
    return list(
        database["changelog"].find(
            {"resource_id": id_, "resource_type": "bibliography"}
        )
    )
