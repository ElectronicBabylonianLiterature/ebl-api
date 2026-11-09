"""Disposable local browser-test server. Never use production data or credentials."""

import os
import uuid

import falcon
from pymongo import MongoClient
from waitress import serve

from ebl import error_handler
from ebl.common.domain.scopes import Scope
from ebl.media.application.default_media_service import DefaultMediaService
from ebl.media.application.media_management import MediaManagementService
from ebl.media.application.media_runtime import MediaRuntime
from ebl.media.infrastructure.grid_fs_media_representation_store import (
    GridFsMediaRepresentationStore,
)
from ebl.media.infrastructure.mongo_media_management import (
    MongoMediaManagementRepository,
)
from ebl.media.infrastructure.upload_images import UploadLimits, prepare_upload
from ebl.media.web.bootstrap import create_media_routes
from ebl.users.infrastructure.auth0 import Auth0User


class TestAuthentication:
    def process_request(self, req, resp):
        if req.method == "OPTIONS":
            return
        role = (req.get_header("Authorization") or "").removeprefix("Bearer ")
        scopes = {
            "contributor": "upload:fragment_media",
            "other": "upload:fragment_media",
            "manager": "manage:fragment_media",
            "reader": "",
        }
        if role not in scopes:
            raise falcon.HTTPUnauthorized()
        req.context["user"] = Auth0User(
            {"sub": f"auth0|{role}", "scope": scopes[role]},
            lambda: {"name": role},
        )


class TestFragments:
    def query_read_scopes(self, number):
        return [Scope.READ_CAIC_FRAGMENTS] if str(number) == "K.2" else []


def main():
    uri = os.environ["MEDIA_E2E_MONGODB_URI"]
    if not uri.startswith("mongodb://ebl-media-upload-test-mongo:"):
        raise RuntimeError(
            "Browser E2E server requires the dedicated disposable test MongoDB."
        )
    client = MongoClient(uri)
    database_name = "media_upload_e2e_" + uuid.uuid4().hex
    database = client[database_name]
    repository = MongoMediaManagementRepository(database)
    repository.create_indexes()
    store = GridFsMediaRepresentationStore(database)
    store.create_indexes()
    management = MediaManagementService(
        repository, store, prepare_upload, UploadLimits()
    )
    runtime = MediaRuntime(DefaultMediaService(repository, store), store, management)
    app = falcon.App(cors_enable=True, middleware=[TestAuthentication()])
    error_handler.set_up(app)
    create_media_routes(app, TestFragments(), runtime)
    try:
        serve(app, host="0.0.0.0", port=8000, max_request_body_size=26 * 1024 * 1024)
    finally:
        client.drop_database(database_name)
        client.close()


if __name__ == "__main__":
    main()
