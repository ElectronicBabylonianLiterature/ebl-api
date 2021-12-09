import json

import falcon

from ebl.tests.factories.annotation import AnnotationsFactory, AnnotationFactory, AnnotationDataFactory


def test_signs_get(client, annotations_repository, photo_repository, when):
    sign_name = "signName"

    annotation_data = AnnotationDataFactory.build(sign_name="signName")
    annotation = AnnotationFactory.build(data=annotation_data)
    annotations_repository.create_or_update(AnnotationsFactory.build(fragment_number="K.2", annotations=[annotation]))

    result = client.simulate_get(f"/signs/{sign_name}/images")

    assert len(json.loads(result.json)) > 0
    assert result.status == falcon.HTTP_OK
    assert result.headers["Access-Control-Allow-Origin"] == "*"



