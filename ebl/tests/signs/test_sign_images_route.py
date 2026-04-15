import falcon

from ebl.fragmentarium.application.cropped_sign_image import CroppedSignImage, Base64

from ebl.fragmentarium.domain.annotation import PcaClustering

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

    annotation_data = AnnotationDataFactory.build(sign_name="signName", path=[2, 0, 0])
    cropped_sign = CroppedSignFactory.build()
    annotation = AnnotationFactory.build(
        data=annotation_data, cropped_sign=cropped_sign
    )
    fragment_number = MuseumNumber("K", "2")
    cropped_sign_images_repository.create_many(
        [
            CroppedSignImage(
                annotation.cropped_sign.image_id,
                Base64("test-base64-string"),
                fragment_number,
            )
        ]
    )
    annotations_repository.create_or_update(
        AnnotationsFactory.build(
            fragment_number=fragment_number, annotations=[annotation]
        )
    )

    result = client.simulate_get("/signs/signName/images")

    assert len(result.json) > 0
    result_json = result.json[0]

    assert result_json["fragmentNumber"] == str(fragment.number)
    assert result_json["image"] == "test-base64-string"
    assert result_json["script"] == str(fragment.script)
    assert result_json["label"] == cropped_sign.label

    assert result.status == falcon.HTTP_OK


def test_signs_get_with_centroids_only(
    client,
    annotations_repository,
    photo_repository,
    fragment_repository,
    text_with_labels,
    cropped_sign_images_repository,
):
    fragment = TransliteratedFragmentFactory.build(
        number=MuseumNumber.of("K.3"), text=text_with_labels
    )
    fragment_repository.create(fragment)

    annotation_data = AnnotationDataFactory.build(sign_name="signName", path=[2, 0, 0])
    cropped_sign = CroppedSignFactory.build()
    annotation = AnnotationFactory.build(
        data=annotation_data,
        cropped_sign=cropped_sign,
        pca_clustering=PcaClustering(
            cluster_id="test-centroid-cluster-id",
            cluster_rank=0,
            form="canonical1",
            is_centroid=True,
            cluster_size=10,
            is_main=True,
        ),
    )

    fragment_number = MuseumNumber("K", "3")
    cropped_sign_images_repository.create_many(
        [
            CroppedSignImage(
                annotation.cropped_sign.image_id,
                Base64("test-base64-string"),
                fragment_number,
            )
        ]
    )
    annotations_repository.create_or_update(
        AnnotationsFactory.build(
            fragment_number=fragment_number, annotations=[annotation]
        )
    )

    result = client.simulate_get("/signs/signName/images?centroids_only=true")

    assert len(result.json) > 0
    assert result.status == falcon.HTTP_OK

def test_signs_get_cluster_without_script_returns_bad_request(client):
    result = client.simulate_get("/signs/signName/images/cluster/test-cluster-id")

    assert result.status == falcon.HTTP_BAD_REQUEST
    assert "script" in result.json["error"].lower()

def test_signs_get_cluster_with_script(
    client,
    annotations_repository,
    photo_repository,
    fragment_repository,
    text_with_labels,
    cropped_sign_images_repository,
):
    fragment = TransliteratedFragmentFactory.build(
        number=MuseumNumber.of("K.4"), text=text_with_labels
    )
    fragment_repository.create(fragment)

    annotation_data = AnnotationDataFactory.build(sign_name="signName", path=[2, 0, 0])
    cropped_sign = CroppedSignFactory.build()
    annotation = AnnotationFactory.build(
        data=annotation_data,
        cropped_sign=cropped_sign,
        pca_clustering=PcaClustering(
            cluster_id="test-cluster-id",
            cluster_rank=0,
            form="canonical1",
            is_centroid=True,
            cluster_size=10,
            is_main=True,
        ),
    )

    fragment_number = MuseumNumber("K", "4")
    cropped_sign_images_repository.create_many(
        [
            CroppedSignImage(
                annotation.cropped_sign.image_id,
                Base64("test-base64-string"),
                fragment_number,
            )
        ]
    )
    annotations_repository.create_or_update(
        AnnotationsFactory.build(
            fragment_number=fragment_number, annotations=[annotation]
        )
    )

    result = client.simulate_get(
        "/signs/signName/images/cluster/test-cluster-id",
        params={"script": fragment.script.period.long_name},
    )

    assert len(result.json) > 0
    assert result.status == falcon.HTTP_OK
    assert result.json[0]["annotationId"] == annotation.data.id