import falcon

from ebl.context import Context
from ebl.fragmentarium.application.cropped_annotations_service import (
    CroppedAnnotationService,
)
from ebl.signs.web.sign_search import SignsSearch
from ebl.signs.web.signs import SignsResource, SignsListResource, SignsOrderResource
from ebl.signs.web.cropped_annotations import CroppedAnnotationsResource


def create_signs_routes(api: falcon.App, context: Context):
    signs_search = SignsSearch(context.sign_repository)
    signs = SignsResource(context.sign_repository)
    ordered_signs = SignsOrderResource(context.sign_repository)
    signs_images = CroppedAnnotationsResource(
        CroppedAnnotationService(
            context.annotations_repository,
            context.cropped_sign_images_repository,
            context.fragment_repository,
        )
    )
    signs_all = SignsListResource(context.sign_repository)
    api.add_route("/signs", signs_search)
    api.add_route("/signs/{sign_name}", signs)
    api.add_route("/signs/{sign_name}/images", signs_images)
    api.add_route("/signs/all", signs_all)
    api.add_route("/signs/{sign_name}/{order}/{sort_era}", ordered_signs)
