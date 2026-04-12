from falcon import Request, Response

from ebl.fragmentarium.application.cropped_annotations_service import (
    CroppedAnnotationService,
)


class CroppedAnnotationsResource:
    def __init__(self, cropped_annotations_service: CroppedAnnotationService):
        self._cropped_annotations_service = cropped_annotations_service

    def on_get(self, req: Request, resp: Response, sign_name: str):
        centroids_only = req.get_param_as_bool("centroids_only", default=False)

        cropped_signs = self._cropped_annotations_service.find_annotations_by_sign(
            sign_name,
            centroids_only=centroids_only,
        )
        resp.media = cropped_signs


class ClusterCroppedAnnotationsResource:
    def __init__(self, cropped_annotations_service: CroppedAnnotationService):
        self._cropped_annotations_service = cropped_annotations_service

    def on_get(self, req: Request, resp: Response, sign_name: str, cluster_id: str):
        script_filter = req.get_param("script")

        if not script_filter:
            resp.status = "400 Bad Request"
            resp.media = {
                "error": "Query parameter 'script' is required for cluster queries"
            }
            return

        cropped_signs = self._cropped_annotations_service.find_annotations_by_sign(
            sign_name,
            centroids_only=False,
            cluster_id=cluster_id,
            script_filter=script_filter,
        )
        resp.media = cropped_signs