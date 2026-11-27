import attr
import falcon
import pytest
from falcon import testing
from falcon_auth import NoneAuthBackend

import ebl.app
from ebl.context import Context
from ebl.errors import NotFoundError
from ebl.signs.application.mes_zl_kap2_repository import (
    MesZlKap2Entry,
    mes_zl_number_variants,
)
from ebl.signs.infrastructure.mongo_mes_zl_kap2_repository import (
    COLLECTION,
    MongoMesZlKap2Repository,
)
from ebl.transliteration.application.sign_repository import SignRepository
from ebl.transliteration.domain.sign import Sign, SignListRecord, SignName
from ebl.users.infrastructure.auth0 import Auth0User

SE_TEXT = "579\t𒊺\t**— ŠE — ŠL 367 — ASy 212**\nFossey p736-739."
ENTRIES = {"_Einleitung": "Kapitel II", "579": SE_TEXT, "214′": "214′\t…"}


def sign(name: str, *lists: SignListRecord) -> Sign:
    return Sign(SignName(name), lists=tuple(lists))


@pytest.fixture
def full_editor_client(context: Context) -> testing.TestClient:
    user = Auth0User(
        {"scope": "read:words read:meszl-kap2"},
        lambda: {"name": "editor@example.com", "https://ebabylon.org/eblName": "E"},
    )
    editor_context = attr.evolve(context, auth_backend=NoneAuthBackend(lambda: user))
    return testing.TestClient(ebl.app.create_app(editor_context))


@pytest.fixture
def imported(database) -> None:
    database[COLLECTION].insert_many(
        [{"_id": number, "text": text} for number, text in ENTRIES.items()]
    )


def test_number_variants() -> None:
    assert mes_zl_number_variants(" 214' ") == ["214'", "214′"]
    assert mes_zl_number_variants("579") == ["579"]


def test_find(mes_zl_kap2_repository: MongoMesZlKap2Repository, imported) -> None:
    assert mes_zl_kap2_repository.find("579") == MesZlKap2Entry("579", SE_TEXT)


def test_find_accepts_apostrophe_for_prime(
    mes_zl_kap2_repository: MongoMesZlKap2Repository, imported
) -> None:
    assert mes_zl_kap2_repository.find("214'").number == "214′"


def test_find_missing(mes_zl_kap2_repository: MongoMesZlKap2Repository) -> None:
    with pytest.raises(NotFoundError):
        mes_zl_kap2_repository.find("1")


def test_route_requires_scope(client, sign_repository: SignRepository) -> None:
    sign_repository.create(sign("ŠE", SignListRecord("MZL", "579")))
    result = client.simulate_get("/signs/ŠE/meszl-kap2")
    assert result.status == falcon.HTTP_FORBIDDEN


def test_route_refuses_guests(guest_client) -> None:
    result = guest_client.simulate_get("/signs/ŠE/meszl-kap2")
    assert result.status == falcon.HTTP_FORBIDDEN


def test_route_returns_entry(
    full_editor_client, sign_repository: SignRepository, imported
) -> None:
    sign_repository.create(
        sign("ŠE", SignListRecord("ABZ", "367"), SignListRecord("MZL", "579"))
    )
    result = full_editor_client.simulate_get("/signs/ŠE/meszl-kap2")
    assert result.status == falcon.HTTP_OK
    assert result.json == {"number": "579", "text": SE_TEXT}
    assert "no-store" in result.headers["Cache-Control"]


def test_route_sign_without_mes_zl_number(
    full_editor_client, sign_repository: SignRepository, imported
) -> None:
    sign_repository.create(sign("X", SignListRecord("ABZ", "1")))
    result = full_editor_client.simulate_get("/signs/X/meszl-kap2")
    assert result.status == falcon.HTTP_NOT_FOUND


def test_route_number_without_entry(
    full_editor_client, sign_repository: SignRepository, imported
) -> None:
    sign_repository.create(sign("Y", SignListRecord("MZL", "999")))
    result = full_editor_client.simulate_get("/signs/Y/meszl-kap2")
    assert result.status == falcon.HTTP_NOT_FOUND
