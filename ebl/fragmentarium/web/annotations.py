import falcon

from ebl.fragmentarium.application.annotations_schema import AnnotationsSchema
from ebl.fragmentarium.application.annotations_service import AnnotationsService
from ebl.fragmentarium.web.dtos import parse_museum_number
from ebl.marshmallowschema import validate
from ebl.users.web.require_scope import require_scope


class AnnotationResource:
    def __init__(self, annotation_service: AnnotationsService):
        self._annotation_service = annotation_service

    @falcon.before(require_scope, "annotate:fragments")
    @validate(AnnotationsSchema(), AnnotationsSchema())
    def on_post(self, req: falcon.Request, resp: falcon.Response, number: str):
        """---
        description: >-
          Creates or updates fragment image annotations. The fragment number in the
          path and in the body mus match.
        requestBody:
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Annotations'
        responses:
          200:
            description: Fragments matching the query
            content:
              application/json:
                schema:
                  $ref: '#/components/schemas/Annotations'
          400:
            description: Request data failed validation.
          422:
            description: Fragment numbers do not match.
        security:
        - auth0:
          - annotate:fragments
        parameters:
        - in: path
          name: number
          required: true
          schema:
            type: string
        """
        if number == req.media.get("fragmentNumber"):
            annotations = self._annotation_service.update(
                AnnotationsSchema().load(req.media), req.context.user
            )
            resp.media = AnnotationsSchema().dump(annotations)
        else:
            raise falcon.HTTPUnprocessableEntity("Fragment numbers do not match.")

    @falcon.before(require_scope, "read:fragments")
    @validate(None, AnnotationsSchema())
    def on_get(self, _, resp: falcon.Response, number: str):
        """---
        description: >-
          Retrieves fragment image annotations.
        responses:
          200:
            description: Annotations for the given fragment number
            content:
              application/json:
                schema:
                  $ref: '#/components/schemas/Annotations'
          422:
            description: Invalid museum number
        security:
        - auth0:
          - read:fragments
        parameters:
        - in: path
          name: number
          required: true
          schema:
            type: string
            pattern: '^.+?\\.[^.]+(\\.[^.]+)?$'
        """
        annotations = self._annotation_service.find(parse_museum_number(number))
        resp.media = AnnotationsSchema().dump(annotations)
