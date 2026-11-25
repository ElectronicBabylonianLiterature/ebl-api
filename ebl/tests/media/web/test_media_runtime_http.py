from threading import Thread
from wsgiref.simple_server import make_server

import requests
from pymongo.database import Database

from ebl.app import create_app
from ebl.context import Context
from ebl.tests.media.web.mongo_test_support import (
    context_with_media,
    png_bytes,
    seed_runtime,
)


def test_running_service_serves_gridfs_media(
    database: Database, context: Context
) -> None:
    runtime, _ = seed_runtime(database, context)
    application = create_app(context_with_media(context, runtime))
    with make_server("127.0.0.1", 0, application) as server:
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            origin = f"http://127.0.0.1:{server.server_port}"
            listing = requests.get(f"{origin}/media?fragment=A%2FB.1", timeout=10)
            assert listing.status_code == 200
            [media] = listing.json()["media"]
            original = requests.get(
                origin + media["representations"]["original"]["url"], timeout=10
            )
            assert original.status_code == 200
            assert original.content == png_bytes()
            assert original.headers["Content-Type"] == "image/png"
        finally:
            server.shutdown()
            thread.join(timeout=10)
        assert not thread.is_alive()
