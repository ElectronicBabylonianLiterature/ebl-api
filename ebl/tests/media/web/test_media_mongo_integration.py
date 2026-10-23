import os

from pymongo import MongoClient
from falcon import testing
from pymongo.database import Database

from ebl.app import create_app
from ebl.context import Context
from ebl.media.web.fragment_media_enricher import FragmentMediaEnricher
from ebl.tests.media.web.helpers import body, get
from ebl.tests.media.web.mongo_test_support import (
    MediaReadCounter,
    context_with_media,
    png_bytes,
    seed_runtime,
)
from ebl.media.web.bootstrap import create_media_runtime


def test_mongo_gridfs_media_round_trip(database: Database, context: Context) -> None:
    runtime, stored = seed_runtime(database, context)
    client = testing.TestClient(create_app(context_with_media(context, runtime)))
    listing = get(client, "/media?fragment=A%2FB.1")
    assert listing.status_code == 200
    [media] = body(listing)["media"]
    assert media["id"] == str(stored.media.id)
    assert media["isPrimary"] is False
    assert media["representations"]["thumbnails"] == {}
    binary = get(client, media["representations"]["original"]["url"])
    assert binary.status_code == 200
    assert binary.content == png_bytes()
    assert (
        get(client, f"/media/{stored.media.id}/display?fragment=A%2FB.1").status_code
        == 404
    )


def test_real_mongo_summary_uses_one_batch_read(
    database: Database, context: Context
) -> None:
    seed_runtime(database, context)
    counter = MediaReadCounter()
    client: MongoClient[dict] = MongoClient(
        os.environ["MONGODB_URI"], event_listeners=[counter]
    )
    with client:
        runtime = create_media_runtime(client[database.name])
        rows: list[dict] = [
            {"museumNumber": {"prefix": "A/B", "number": "1", "suffix": ""}},
            {
                "museumNumber": {"prefix": "K", "number": "99", "suffix": ""},
                "hasPhoto": True,
            },
        ]
        enriched = FragmentMediaEnricher(runtime.service).enrich_rows(rows)
    assert counter.count == 1
    assert enriched[0]["mediaSummary"] == {"count": 1, "types": ["PHOTO"]}
    assert enriched[1]["mediaSummary"] == {"count": 0, "types": []}
    assert enriched[1]["hasPhoto"] is True


def test_api_construction_does_not_create_media_indexes(database: Database) -> None:
    create_media_runtime(database)
    assert database.list_collection_names() == []
