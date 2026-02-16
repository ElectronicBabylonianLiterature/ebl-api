import falcon

from ebl.fragmentarium.application.annotations_schema import (
    AnnotationsSchema,
)
from ebl.fragmentarium.application.annotations_service import AnnotationsService
from ebl.fragmentarium.web.dtos import parse_museum_number
from ebl.marshmallowschema import validate
from ebl.users.web.require_scope import require_scope


class AnnotationResource:
    def __init__(self, annotation_service: AnnotationsService):
        self._annotation_service = annotation_service

    @falcon.before(require_scope, "annotate:fragments")
    @validate(AnnotationsSchema())
    def on_post(self, req: falcon.Request, resp: falcon.Response, number: str):
        if number == req.media.get("fragmentNumber"):
            annotations = self._annotation_service.update(
                AnnotationsSchema().load(req.media), req.context.user
            )
            resp.media = AnnotationsSchema().dump(annotations)
        else:
            raise falcon.HTTPUnprocessableEntity(
                description="Fragment numbers do not match."
            )

    @validate(None, AnnotationsSchema())
    def on_get(self, req, resp: falcon.Response, number: str):
        museum_number = parse_museum_number(number)
        if req.params.get("generateAnnotations") == "true":
            annotations = self._annotation_service.generate_annotations(museum_number)
        else:
            annotations = self._annotation_service.find(museum_number)
        resp.media = AnnotationsSchema().dump(annotations)
