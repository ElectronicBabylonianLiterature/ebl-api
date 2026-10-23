import falcon
from pymongo.database import Database

from ebl.fragmentarium.application.fragment_repository import FragmentRepository
from ebl.media.application.default_media_service import DefaultMediaService
from ebl.media.application.media_runtime import MediaRuntime
from ebl.media.web.resources import MediaResource


def create_media_runtime(database: Database) -> MediaRuntime:
    from ebl.media.infrastructure.grid_fs_media_representation_store import (
        GridFsMediaRepresentationStore,
    )
    from ebl.media.infrastructure.mongo_media_repository import MongoMediaRepository

    repository = MongoMediaRepository(database)
    store = GridFsMediaRepresentationStore(database)
    return MediaRuntime(DefaultMediaService(repository, store), store)


def create_media_routes(
    api: falcon.App, fragments: FragmentRepository, runtime: MediaRuntime
) -> None:
    resource = MediaResource(fragments, runtime)
    api.add_route("/media", resource)
    api.add_route("/media/{media_id}/{representation}", resource, suffix="binary")
    api.add_route(
        "/media/{media_id}/thumbnail/{size}",
        resource,
        suffix="thumbnail",
    )
