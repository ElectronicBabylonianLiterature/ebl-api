import pytest

from ebl.files.application.file_repository import FileRepository
from ebl.fragmentarium.application.annotations_repository import AnnotationsRepository
from ebl.fragmentarium.application.cropped_sign_image import CroppedSignImage, Base64
from ebl.fragmentarium.application.cropped_sign_images_repository import (
    CroppedSignImagesRepository,
)
from ebl.fragmentarium.application.fragment_repository import FragmentRepository
from ebl.fragmentarium.domain.annotation import PcaClustering
from ebl.tests.factories.annotation import (
    AnnotationsFactory,
    AnnotationFactory,
    AnnotationDataFactory,
    CroppedSignFactory,
)
from ebl.tests.factories.fragment import TransliteratedFragmentFactory
from ebl.transliteration.domain.museum_number import MuseumNumber
from ebl.transliteration.domain.text import Text


@pytest.fixture
def centroid_and_unclustered_sign_images(
    annotations_repository: AnnotationsRepository,
    photo_repository: FileRepository,
    fragment_repository: FragmentRepository,
    text_with_labels: Text,
    cropped_sign_images_repository: CroppedSignImagesRepository,
) -> None:
    fragment = TransliteratedFragmentFactory.build(
        number=MuseumNumber.of("K.5"), text=text_with_labels
    )
    fragment_repository.create(fragment)

    centroid_annotation = AnnotationFactory.build(
        data=AnnotationDataFactory.build(sign_name="signName", path=[2, 0, 0]),
        cropped_sign=CroppedSignFactory.build(image_id="centroid-image"),
        pca_clustering=PcaClustering(
            cluster_id="test-centroid-cluster-id",
            cluster_rank=0,
            form="canonical1",
            is_centroid=True,
            cluster_size=10,
            is_main=True,
        ),
    )
    unclustered_annotation = AnnotationFactory.build(
        data=AnnotationDataFactory.build(sign_name="signName", path=[2, 0, 1]),
        cropped_sign=CroppedSignFactory.build(image_id="unclustered-image"),
        pca_clustering=None,
    )

    fragment_number = MuseumNumber("K", "5")
    cropped_sign_images_repository.create_many(
        [
            CroppedSignImage(
                centroid_annotation.cropped_sign.image_id,
                Base64("centroid-base64-string"),
                fragment_number,
            ),
            CroppedSignImage(
                unclustered_annotation.cropped_sign.image_id,
                Base64("unclustered-base64-string"),
                fragment_number,
            ),
        ]
    )
    annotations_repository.create_or_update(
        AnnotationsFactory.build(
            fragment_number=fragment_number,
            annotations=[centroid_annotation, unclustered_annotation],
        )
    )
