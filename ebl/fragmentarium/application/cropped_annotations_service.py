from typing import Optional, Sequence

import attr

from ebl.fragmentarium.application.annotations_repository import AnnotationsRepository
from ebl.fragmentarium.application.annotations_schema import PcaClusteringSchema
from ebl.fragmentarium.application.cropped_sign_images_repository import (
    CroppedSignImagesRepository,
)
from ebl.fragmentarium.application.fragment_repository import FragmentRepository
from ebl.fragmentarium.domain.annotation import AnnotationValueType
from ebl.fragmentarium.domain.date import DateSchema


class CroppedAnnotationService:
    def __init__(
        self,
        annotations_repository: AnnotationsRepository,
        cropped_sign_images_repository: CroppedSignImagesRepository,
        fragment_repository: FragmentRepository,
    ):
        self._annotations_repository = annotations_repository
        self._fragment_repository = fragment_repository
        self._cropped_sign_image_repository = cropped_sign_images_repository

    def find_annotations_by_sign(
        self,
        sign: str,
        centroids_only: bool = False,
        cluster_id: Optional[str] = None,
        script_filter: Optional[str] = None,
    ) -> Sequence[dict]:
        annotations = self._annotations_repository.find_by_sign(
            sign, centroids_only, cluster_id, script_filter
        )
        cropped_image_annotations = []

        for annotation in annotations:
            date = DateSchema().dump(
                self._fragment_repository.fetch_date(annotation.fragment_number)
            )
            annotation = attr.evolve(
                annotation,
                annotations=[
                    x
                    for x in annotation.annotations
                    if x.data.type == AnnotationValueType.HAS_SIGN
                ],
            )

            for annotation_elem in annotation.annotations:
                if cropped_sign := annotation_elem.cropped_sign:
                    try:
                        cropped_sign_image = (
                            self._cropped_sign_image_repository.query_by_id(
                                cropped_sign.image_id
                            )
                        )

                        response = {
                            "fragmentNumber": str(annotation.fragment_number),
                            "image": cropped_sign_image.image,
                            "script": str(annotation.script),
                            "label": cropped_sign.label,
                            "date": date,
                            "provenance": annotation.provenance,
                            "annotationId": annotation_elem.data.id,
                        }

                        if annotation_elem.pca_clustering:
                            response["pcaClustering"] = PcaClusteringSchema().dump(
                                annotation_elem.pca_clustering
                            )

                        cropped_image_annotations.append(response)
                    except Exception:
                        pass

        return cropped_image_annotations