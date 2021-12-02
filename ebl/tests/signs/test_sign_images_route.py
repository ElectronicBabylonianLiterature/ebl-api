import json

import falcon

from ebl.tests.factories.annotation import AnnotationsFactory, AnnotationFactory, AnnotationDataFactory


def test_signs_get(client, annotations_repository, photo_repository, when):
    sign_name = "signName"

    annotation_data = AnnotationDataFactory.build(sign_name="signName")
    annotation = AnnotationFactory.build(data=annotation_data)
    annotations_repository.create_or_update(AnnotationsFactory.build(fragment_number="K.2", annotations=[annotation]))

    result = client.simulate_get(f"/signs/{sign_name}/image")

    photo = photo_repository.query_by_file_name("K.2.jpg")
    x = json.loads(result.json)
    assert result.status == falcon.HTTP_OK
    assert result.headers["Access-Control-Allow-Origin"] == "*"



