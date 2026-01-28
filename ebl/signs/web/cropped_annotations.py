from ebl.fragmentarium.application.cropped_annotations_service import (
    CroppedAnnotationService,
)


class CroppedAnnotationsResource:
    def __init__(self, cropped_annotations_service: CroppedAnnotationService):
        self._cropped_annotations_service = cropped_annotations_service

    def on_get(self, _req, resp, sign_name):
        cropped_signs = self._cropped_annotations_service.find_annotations_by_sign(
            sign_name
        )
        resp.media = cropped_signs
