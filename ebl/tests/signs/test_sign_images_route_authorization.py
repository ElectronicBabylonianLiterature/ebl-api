import falcon
import pytest

from ebl.common.domain.scopes import Scope
from ebl.fragmentarium.application.cropped_sign_image import Base64, CroppedSignImage
from ebl.fragmentarium.domain.annotation import PcaClustering
from ebl.tests.factories.annotation import (
    AnnotationDataFactory,
    AnnotationFactory,
    AnnotationsFactory,
    CroppedSignFactory,
)
from ebl.tests.factories.fragment import TransliteratedFragmentFactory
from ebl.transliteration.domain.museum_number import MuseumNumber

SIGN_NAME = "restrictedSignName"
CLUSTER_ID = "restricted-cluster-id"

CLUSTERING = PcaClustering(
    cluster_id=CLUSTER_ID,
    cluster_rank=0,
    form="canonical1",
    is_centroid=True,
    cluster_size=10,
    is_main=True,
)


def _create_annotated_fragment(
    annotations_repository,
    cropped_sign_images_repository,
    fragment_repository,
    text_with_labels,
    number,
    authorized_scopes,
):
    fragment = TransliteratedFragmentFactory.build(
        number=number, text=text_with_labels, authorized_scopes=authorized_scopes
    )
    fragment_repository.create(fragment)

    annotation = AnnotationFactory.build(
        data=AnnotationDataFactory.build(sign_name=SIGN_NAME, path=[2, 0, 0]),
        cropped_sign=CroppedSignFactory.build(),
        pca_clustering=CLUSTERING,
    )
    cropped_sign_images_repository.create_many(
        [
            CroppedSignImage(
                annotation.cropped_sign.image_id,
                Base64("restricted-base64-string"),
                number,
            )
        ]
    )
    annotations_repository.create_or_update(
        AnnotationsFactory.build(fragment_number=number, annotations=[annotation])
    )
    return fragment


@pytest.fixture
def make_annotated_fragment(
    annotations_repository,
    cropped_sign_images_repository,
    fragment_repository,
    text_with_labels,
):
    def _make(number, authorized_scopes):
        return _create_annotated_fragment(
            annotations_repository,
            cropped_sign_images_repository,
            fragment_repository,
            text_with_labels,
            number,
            authorized_scopes,
        )

    return _make


def test_public_fragment_images_are_returned(client, make_annotated_fragment):
    fragment = make_annotated_fragment(MuseumNumber.of("K.301"), [])

    result = client.simulate_get(f"/signs/{SIGN_NAME}/images")

    assert result.status == falcon.HTTP_OK
    assert [item["fragmentNumber"] for item in result.json] == [str(fragment.number)]


def test_authorized_restricted_fragment_images_are_returned(
    client, make_annotated_fragment
):
    fragment = make_annotated_fragment(
        MuseumNumber.of("K.302"), [Scope.READ_CAIC_FRAGMENTS]
    )

    result = client.simulate_get(f"/signs/{SIGN_NAME}/images")

    assert result.status == falcon.HTTP_OK
    assert [item["fragmentNumber"] for item in result.json] == [str(fragment.number)]


def test_unauthorized_restricted_fragment_images_are_hidden(
    client, make_annotated_fragment
):
    make_annotated_fragment(MuseumNumber.of("K.303"), [Scope.READ_COPENHAGEN_FRAGMENTS])

    result = client.simulate_get(f"/signs/{SIGN_NAME}/images")

    assert result.status == falcon.HTTP_OK
    assert result.json == []


def test_restricted_fragment_images_are_hidden_from_guest(
    guest_client, make_annotated_fragment
):
    make_annotated_fragment(MuseumNumber.of("K.304"), [Scope.READ_CAIC_FRAGMENTS])

    result = guest_client.simulate_get(f"/signs/{SIGN_NAME}/images")

    assert result.status == falcon.HTTP_OK
    assert result.json == []


def test_public_fragment_images_are_returned_to_guest(
    guest_client, make_annotated_fragment
):
    fragment = make_annotated_fragment(MuseumNumber.of("K.305"), [])

    result = guest_client.simulate_get(f"/signs/{SIGN_NAME}/images")

    assert result.status == falcon.HTTP_OK
    assert [item["fragmentNumber"] for item in result.json] == [str(fragment.number)]


def test_public_fragment_cluster_images_are_returned(client, make_annotated_fragment):
    fragment = make_annotated_fragment(MuseumNumber.of("K.306"), [])

    result = client.simulate_get(
        f"/signs/{SIGN_NAME}/images/cluster/{CLUSTER_ID}",
        params={"script": fragment.script.period.long_name},
    )

    assert result.status == falcon.HTTP_OK
    assert [item["fragmentNumber"] for item in result.json] == [str(fragment.number)]


def test_unauthorized_restricted_fragment_cluster_images_are_hidden(
    client, make_annotated_fragment
):
    fragment = make_annotated_fragment(
        MuseumNumber.of("K.307"), [Scope.READ_COPENHAGEN_FRAGMENTS]
    )

    result = client.simulate_get(
        f"/signs/{SIGN_NAME}/images/cluster/{CLUSTER_ID}",
        params={"script": fragment.script.period.long_name},
    )

    assert result.status == falcon.HTTP_OK
    assert result.json == []
