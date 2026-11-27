from typing import cast

import attr
import falcon
import pytest
from falcon import testing
from falcon_auth import NoneAuthBackend

import ebl.app
from ebl.context import Context
from ebl.signs.domain.mes_zl_kap2 import MesZlKap2Entry
from ebl.tests.signs.mes_zl_kap2_data import FIRST, PRIMED, SECOND, SHARED
from ebl.transliteration.application.sign_repository import SignRepository
from ebl.transliteration.domain.sign import Sign, SignListRecord, SignName
from ebl.users.infrastructure.auth0 import Auth0User

BASE_SCOPES = "read:words"


def sign(name: str, *lists: SignListRecord) -> Sign:
    return Sign(SignName(name), lists=tuple(lists))


def client_with_scopes(context: Context, scopes: str) -> testing.TestClient:
    user = Auth0User(
        {"scope": scopes},
        lambda: {"name": "editor@example.com", "https://ebabylon.org/eblName": "E"},
    )
    editor_context = attr.evolve(context, auth_backend=NoneAuthBackend(lambda: user))
    return testing.TestClient(ebl.app.create_app(editor_context))


@pytest.fixture
def full_editor_client(context: Context) -> testing.TestClient:
    return client_with_scopes(context, f"{BASE_SCOPES} read:meszl-kap2")


@pytest.fixture
def client_without_scope(context: Context) -> testing.TestClient:
    return client_with_scopes(context, BASE_SCOPES)


def get(client: testing.TestClient, path: str) -> testing.Result:
    return cast(testing.Result, client.simulate_get(path))


def entries_json(*entries: MesZlKap2Entry) -> list[dict[str, str]]:
    return [{"number": entry.number, "text": entry.text} for entry in entries]


@pytest.mark.usefixtures("mes_zl_kap2_entries")
def test_returns_the_entries_of_all_mes_zl_numbers(
    full_editor_client: testing.TestClient, sign_repository: SignRepository
) -> None:
    sign_repository.create(
        sign(
            "ŠE",
            SignListRecord("ABZ", "367"),
            SignListRecord("MZL", "579"),
            SignListRecord("MZL", "580"),
            SignListRecord("MZL", "579"),
        )
    )
    result = get(full_editor_client, "/signs/ŠE/meszl-kap2")
    assert result.status == falcon.HTTP_OK
    assert result.json == entries_json(FIRST, SECOND)
    assert result.headers["Cache-Control"] == "private, no-store"


@pytest.mark.usefixtures("mes_zl_kap2_entries")
def test_resolves_apostrophes_and_aliases(
    full_editor_client: testing.TestClient, sign_repository: SignRepository
) -> None:
    sign_repository.create(
        sign("X", SignListRecord("MZL", "214'"), SignListRecord("MZL", "115a"))
    )
    result = get(full_editor_client, "/signs/X/meszl-kap2")
    assert result.json == entries_json(PRIMED, SHARED)


@pytest.mark.usefixtures("mes_zl_kap2_entries")
def test_sign_without_entries(
    full_editor_client: testing.TestClient, sign_repository: SignRepository
) -> None:
    sign_repository.create(sign("Y", SignListRecord("ABZ", "1")))
    result = get(full_editor_client, "/signs/Y/meszl-kap2")
    assert result.status == falcon.HTTP_OK
    assert result.json == []


def test_unknown_sign(full_editor_client: testing.TestClient) -> None:
    result = get(full_editor_client, "/signs/NOSUCH/meszl-kap2")
    assert result.status == falcon.HTTP_NOT_FOUND


@pytest.mark.usefixtures("mes_zl_kap2_entries")
def test_requires_the_scope(
    client_without_scope: testing.TestClient, sign_repository: SignRepository
) -> None:
    sign_repository.create(sign("ŠE", SignListRecord("MZL", "579")))
    result = get(client_without_scope, "/signs/ŠE/meszl-kap2")
    assert result.status == falcon.HTTP_FORBIDDEN
    assert FIRST.text not in result.text
    assert "Cache-Control" not in result.headers


def test_checks_the_scope_before_the_sign(
    client_without_scope: testing.TestClient,
) -> None:
    result = get(client_without_scope, "/signs/NOSUCH/meszl-kap2")
    assert result.status == falcon.HTTP_FORBIDDEN


def test_refuses_guests(guest_client: testing.TestClient) -> None:
    result = get(guest_client, "/signs/NOSUCH/meszl-kap2")
    assert result.status == falcon.HTTP_FORBIDDEN
