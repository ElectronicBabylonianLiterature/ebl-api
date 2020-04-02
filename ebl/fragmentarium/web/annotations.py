import falcon  # pyre-ignore

from ebl.fragmentarium.application.annotations_schema import AnnotationsSchema
from ebl.fragmentarium.domain.fragment import FragmentNumber
from ebl.marshmallowschema import validate
from ebl.users.web.require_scope import require_scope


class AnnotationResource:
    def __init__(self, annotation_service):
        self._annotation_service = annotation_service

    @falcon.before(require_scope, "annotate:fragments")
    @validate(AnnotationsSchema(), AnnotationsSchema())
    def on_post(
        self,
        req: falcon.Request,  # pyre-ignore[11]
        resp: falcon.Response,  # pyre-ignore[11]
        number: str
    ):
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
                AnnotationsSchema().load(req.media), req.context.user  # pyre-ignore[16]
            )
            resp.media = AnnotationsSchema().dump(annotations)  # pyre-ignore[16]
        else:
            raise falcon.HTTPUnprocessableEntity("Fragment numbers do not match.")

    @falcon.before(require_scope, "read:fragments")
    @validate(None, AnnotationsSchema())
    def on_get(self, _, resp: falcon.Response, number: str):  # pyre-ignore[11]
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
        security:
        - auth0:
          - read:fragments
        parameters:
        - in: path
          name: number
          required: true
          schema:
            type: string
        """
        annotations = self._annotation_service.find(FragmentNumber(number))
        resp.media = AnnotationsSchema().dump(annotations)  # pyre-ignore[16]
