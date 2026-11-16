from typing import cast
import falcon
from falcon import testing
from falcon_auth import FalconAuthMiddleware, NoneAuthBackend
from ebl.fragmentarium.application.fragment_repository import FragmentRepository
from ebl.media.web.bootstrap import create_media_routes
from ebl.tests.media.test_media_management_uploads import (
    Fragments,
)
from ebl.users.domain.user import Guest


def test_review_preflight_accepts_if_match(management_runtime):
    app = falcon.App(
        cors_enable=True,
        middleware=[FalconAuthMiddleware(NoneAuthBackend(Guest))],
    )
    create_media_routes(app, cast(FragmentRepository, Fragments()), management_runtime)
    response = testing.TestClient(app).simulate_options(
        "/media/550e8400-e29b-41d4-a716-446655440000/publish?fragment=K.1",
        headers={
            "Origin": "https://www.ebl.lmu.de",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "authorization, content-type, if-match",
        },
    )
    assert response.status_code == 200
    assert "if-match" in response.headers["Access-Control-Allow-Headers"].lower()
