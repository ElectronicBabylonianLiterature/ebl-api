import falcon

from ebl.fragmentarium.domain.museum_number import MuseumNumber
from ebl.tests.factories.annotation import AnnotationsFactory, AnnotationFactory, \
    AnnotationDataFactory
from ebl.tests.factories.fragment import TransliteratedFragmentFactory


def test_signs_get(client, annotations_repository, photo_repository, when, fragment_repository):
    fragment = TransliteratedFragmentFactory.build(number=MuseumNumber.of("K.2"))
    fragment_repository.create(fragment)

    sign_name = "signName"

    annotation_data = AnnotationDataFactory.build(sign_name="signName")
    annotation = AnnotationFactory.build(data=annotation_data)
    annotations_repository.create_or_update(AnnotationsFactory.build(fragment_number="K.2", annotations=[annotation]))

    result = client.simulate_get(f"/signs/{sign_name}/images")

    assert len(result.json) > 0
    result_json = result.json[0]



    assert result_json["fragment_number"] == str(fragment.number)
    assert isinstance(result_json["image"], str)
    assert result_json["script"] == fragment.script
    assert isinstance(result_json["label"], str)

    assert result.status == falcon.HTTP_OK
    assert result.headers["Access-Control-Allow-Origin"] == "*"



