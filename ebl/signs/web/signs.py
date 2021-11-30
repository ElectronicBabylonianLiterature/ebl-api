import falcon

from ebl.fragmentarium.application.annotations_image_extractor import AnnotationImageExtractor
from ebl.users.web.require_scope import require_scope


class SignsImageResource:
    def __init__(self, annotation_image_extractor: AnnotationImageExtractor):
        self._image_extractor = annotation_image_extractor

    @falcon.before(require_scope, "read:words")
    def on_get(self, _req, resp, sign_name):
        images = self._image_extractor.cropped_images_from_sign(sign_name)

