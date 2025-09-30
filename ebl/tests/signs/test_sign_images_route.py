import falcon

from ebl.fragmentarium.application.cropped_sign_image import CroppedSignImage, Base64

from ebl.tests.factories.annotation import (
    AnnotationsFactory,
    AnnotationFactory,
    AnnotationDataFactory,
    CroppedSignFactory,
)
from ebl.tests.factories.fragment import TransliteratedFragmentFactory
from ebl.transliteration.domain.museum_number import MuseumNumber


def test_signs_get(
    client,
    annotations_repository,
    photo_repository,
    fragment_repository,
    text_with_labels,
    cropped_sign_images_repository,
):
    fragment = TransliteratedFragmentFactory.build(
        number=MuseumNumber.of("K.2"), text=text_with_labels
    )
    fragment_repository.create(fragment)

    annotation_data = AnnotationDataFactory.build(
        sign_name="signName", path=[2, 0, 0])
    cropped_sign = CroppedSignFactory.build()
    annotation = AnnotationFactory.build(
        data=annotation_data, cropped_sign=cropped_sign
    )
    fragment_number = MuseumNumber("K", "2")
    cropped_sign_images_repository.create_many(
        [
            CroppedSignImage(
                annotation.cropped_sign.image_id, Base64(
                    "test-base64-string"), fragment_number
            )
        ]
    )
    annotations_repository.create_or_update(
        AnnotationsFactory.build(
            fragment_number=fragment_number, annotations=[annotation])
    )

    result = client.simulate_get("/signs/signName/images")

    assert len(result.json) > 0
    result_json = result.json[0]

    assert result_json["fragmentNumber"] == str(fragment.number)
    assert result_json["image"] == "test-base64-string"
    assert result_json["script"] == str(fragment.script)
    assert result_json["label"] == cropped_sign.label

    assert result.status == falcon.HTTP_OK
