import falcon

from ebl.context import Context
from ebl.fragmentarium.application.cropped_annotations_service import (
    CroppedAnnotationService,
)
from ebl.signs.web.sign_search import SignsSearch
from ebl.signs.web.signs import SignsResource
from ebl.signs.web.cropped_annotations import CroppedAnnotationsResource


def create_signs_routes(api: falcon.App, context: Context):
    signs_search = SignsSearch(context.sign_repository)
    signs = SignsResource(context.sign_repository)
    signs_images = CroppedAnnotationsResource(
        CroppedAnnotationService(
            context.annotations_repository, context.cropped_sign_images_repository
        )
    )
    api.add_route("/signs", signs_search)
    api.add_route("/signs/{sign_name}", signs)
    api.add_route("/signs/{sign_name}/images", signs_images)
