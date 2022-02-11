import falcon

from ebl.context import Context
from ebl.fragmentarium.application.annotations_image_extractor import (
    AnnotationImageExtractor,
)
from ebl.signs.web.sign_search import SignsSearch
from ebl.signs.web.signs import SignsResource
from ebl.signs.web.sign_images import SignsImageResource


def create_signs_routes(api: falcon.App, context: Context):
    signs_search = SignsSearch(context.sign_repository)
    signs = SignsResource(context.sign_repository)
    signs_images = SignsImageResource(
        AnnotationImageExtractor(
            context.fragment_repository,
            context.annotations_repository,
            context.photo_repository,
        )
    )
    api.add_route("/signs", signs_search)
    api.add_route("/signs/{sign_name}", signs)
    api.add_route("/signs/{sign_name}/images", signs_images)
