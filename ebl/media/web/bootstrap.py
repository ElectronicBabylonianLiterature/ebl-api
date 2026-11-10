import falcon
import os
from pymongo.database import Database

from ebl.fragmentarium.application.fragment_repository import FragmentRepository
from ebl.media.application.default_media_service import DefaultMediaService
from ebl.media.application.media_runtime import MediaRuntime
from ebl.media.web.resources import MediaResource


def create_media_runtime(database: Database) -> MediaRuntime:
    from ebl.media.infrastructure.grid_fs_media_representation_store import (
        GridFsMediaRepresentationStore,
    )
    from ebl.media.infrastructure.mongo_media_management import (
        MongoMediaManagementRepository,
    )
    from ebl.media.application.media_management import MediaManagementService
    from ebl.media.infrastructure.upload_images import prepare_upload, UploadLimits

    repository = MongoMediaManagementRepository(database)
    store = GridFsMediaRepresentationStore(database)
    management = None
    if os.environ.get("MEDIA_UPLOAD_ENABLED", "false").lower() == "true":
        management = MediaManagementService(
            repository,
            store,
            prepare_upload,
            UploadLimits(
                max_bytes=int(
                    os.environ.get("MEDIA_UPLOAD_MAX_BYTES", str(25 * 1024 * 1024))
                ),
                max_pixels=int(os.environ.get("MEDIA_UPLOAD_MAX_PIXELS", "40000000")),
                max_dimension=int(
                    os.environ.get("MEDIA_UPLOAD_MAX_DIMENSION", "20000")
                ),
            ),
        )
    return MediaRuntime(DefaultMediaService(repository, store), store, management)


def create_media_routes(
    api: falcon.App, fragments: FragmentRepository, runtime: MediaRuntime
) -> None:
    resource = MediaResource(fragments, runtime)
    api.add_route("/media", resource)
    if runtime.management is not None:
        api.add_route("/media/{media_id}", resource, suffix="item")
    api.add_route("/media/{media_id}/{representation}", resource, suffix="binary")
    api.add_route(
        "/media/{media_id}/thumbnail/{size}",
        resource,
        suffix="thumbnail",
    )
