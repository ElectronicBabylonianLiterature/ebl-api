import falcon

from ebl.context import Context
from ebl.fragmentarium.application.fragment_finder import FragmentFinder
from ebl.media.web.fragment_media import FragmentMediaResource
from ebl.media.web.fragment_media_binaries import (
    FragmentMediaDisplayResource,
    FragmentMediaFileResource,
    FragmentMediaThumbnailResource,
)


def create_media_routes(
    api: falcon.App, context: Context, finder: FragmentFinder
) -> None:
    context.media_repository.create_indexes()
    context.media_representation_store.create_indexes()

    service = context.get_media_service()
    store = context.media_representation_store

    routes = [
        ("/fragments/{number}/media", FragmentMediaResource(service, finder)),
        (
            "/fragments/{number}/media/{media_id}/file",
            FragmentMediaFileResource(service, finder, store),
        ),
        (
            "/fragments/{number}/media/{media_id}/display",
            FragmentMediaDisplayResource(service, finder, store),
        ),
        (
            "/fragments/{number}/media/{media_id}/thumbnail/{size}",
            FragmentMediaThumbnailResource(service, finder, store),
        ),
    ]

    for uri, resource in routes:
        api.add_route(uri, resource)
