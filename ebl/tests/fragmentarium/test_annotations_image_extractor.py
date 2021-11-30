import io

from PIL import Image

from ebl.fragmentarium.application.annotations_image_extractor import AnnotationImageExtractor
from ebl.tests.conftest import FakeFile
from ebl.tests.factories.annotation import AnnotationsFactory


def test_cropped_images_from_sign(annotations_repository, photo_repository, photo_jpeg, when):
    image = Image.open("ebl/tests/test_image.jpeg")
    buf = io.BytesIO()
    image.save(buf, format="JPEG")
    file = FakeFile("1.jpg", buf.getvalue(), {})

    image_extractor = AnnotationImageExtractor(annotations_repository, photo_repository)

    annotation = AnnotationsFactory.build()
    sign = "test-sign"

    (when(photo_repository).query_by_file_name(f"{annotation.fragment_number}.jpg").thenReturn(file))
    (when(annotations_repository).find_by_sign(sign).thenReturn([annotation]))
    result = image_extractor.cropped_images_from_sign(sign)
    assert len(result) > 0
