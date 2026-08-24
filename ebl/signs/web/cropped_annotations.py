from typing import List

import falcon
from falcon import Request, Response

from ebl.common.domain.period import Period
from ebl.common.domain.scopes import Scope
from ebl.fragmentarium.application.cropped_annotations_service import (
    CroppedAnnotationService,
)
from ebl.users.domain.user import User

ABBREV_TO_NAME = {period.value[1]: period.value[0] for period in Period}


def fragment_read_scopes(req: Request) -> List[Scope]:
    user: User = req.context["user"]
    return user.get_scopes(prefix="read:", suffix="-fragments")


class CroppedAnnotationsResource:
    def __init__(self, cropped_annotations_service: CroppedAnnotationService):
        self._cropped_annotations_service = cropped_annotations_service

    def on_get(self, req: Request, resp: Response, sign_name: str):
        centroids_only = req.get_param_as_bool("centroids_only", default=False)
        include_unclustered = req.get_param_as_bool(
            "include_unclustered", default=False
        )

        cropped_signs = self._cropped_annotations_service.find_annotations_by_sign(
            sign_name,
            centroids_only=centroids_only,
            include_unclustered=include_unclustered,
            user_scopes=fragment_read_scopes(req),
        )
        resp.media = cropped_signs


class ClusterCroppedAnnotationsResource:
    def __init__(self, cropped_annotations_service: CroppedAnnotationService):
        self._cropped_annotations_service = cropped_annotations_service

    def on_get(self, req: Request, resp: Response, sign_name: str, cluster_id: str):
        script_filter = req.get_param("script")

        if not script_filter:
            resp.status = falcon.HTTP_BAD_REQUEST
            resp.media = {
                "error": "Query parameter 'script' is required for cluster queries"
            }
            return

        script_filter = ABBREV_TO_NAME.get(script_filter, script_filter)

        cropped_signs = self._cropped_annotations_service.find_annotations_by_sign(
            sign_name,
            centroids_only=False,
            include_unclustered=False,
            cluster_id=cluster_id,
            script_filter=script_filter,
            user_scopes=fragment_read_scopes(req),
        )
        resp.media = cropped_signs
