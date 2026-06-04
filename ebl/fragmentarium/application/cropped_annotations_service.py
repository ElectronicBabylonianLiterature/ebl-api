from typing import Dict, List, Optional, Sequence

import attr

from ebl.fragmentarium.application.annotations_repository import AnnotationsRepository
from ebl.fragmentarium.application.annotations_schema import PcaClusteringSchema
from ebl.fragmentarium.application.cropped_sign_image import CroppedSignImage
from ebl.fragmentarium.application.cropped_sign_images_repository import (
    CroppedSignImagesRepository,
)
from ebl.fragmentarium.application.fragment_repository import FragmentRepository
from ebl.fragmentarium.domain.annotation import (
    Annotation,
    Annotations,
    AnnotationValueType,
)
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

    def _filter_has_sign_annotations(self, annotations: Annotations) -> Annotations:
        return attr.evolve(
            annotations,
            annotations=[
                annotation
                for annotation in annotations.annotations
                if annotation.data.type == AnnotationValueType.HAS_SIGN
            ],
        )

    def _find_fragment_date(
        self, annotations: Annotations, date_cache: Dict[str, dict]
    ) -> dict:
        fragment_number = str(annotations.fragment_number)
        if fragment_number not in date_cache:
            date_cache[fragment_number] = DateSchema().dump(
                self._fragment_repository.fetch_date(annotations.fragment_number)
            )
        return date_cache[fragment_number]

    def _find_cropped_sign_image(
        self, image_id: str, image_cache: Dict[str, CroppedSignImage]
    ) -> Optional[CroppedSignImage]:
        try:
            if image_id not in image_cache:
                image_cache[image_id] = self._cropped_sign_image_repository.query_by_id(
                    image_id
                )
            return image_cache[image_id]
        except Exception:
            return None

    def _build_response(
        self,
        annotations: Annotations,
        annotation: Annotation,
        image: CroppedSignImage,
        date: dict,
    ) -> dict:
        response = {
            "fragmentNumber": str(annotations.fragment_number),
            "image": image.image,
            "script": str(annotations.script),
            "label": annotation.cropped_sign.label,
            "date": date,
            "provenance": annotations.provenance,
            "annotationId": annotation.data.id,
        }

        if annotation.pca_clustering:
            response["pcaClustering"] = PcaClusteringSchema().dump(
                annotation.pca_clustering
            )

        return response

    def find_annotations_by_sign(
        self,
        sign: str,
        centroids_only: bool = False,
        include_unclustered: bool = False,
        cluster_id: Optional[str] = None,
        script_filter: Optional[str] = None,
    ) -> Sequence[dict]:
        annotations = self._annotations_repository.find_by_sign(
            sign, centroids_only, include_unclustered, cluster_id, script_filter
        )
        cropped_image_annotations: List[dict] = []
        date_cache: Dict[str, dict] = {}
        image_cache: Dict[str, CroppedSignImage] = {}

        for annotation_group in annotations:
            filtered_annotations = self._filter_has_sign_annotations(annotation_group)
            date = self._find_fragment_date(filtered_annotations, date_cache)

            for annotation in filtered_annotations.annotations:
                cropped_sign = annotation.cropped_sign
                if cropped_sign is None:
                    continue

                image = self._find_cropped_sign_image(
                    cropped_sign.image_id, image_cache
                )
                if image is None:
                    continue

                cropped_image_annotations.append(
                    self._build_response(filtered_annotations, annotation, image, date)
                )

        return cropped_image_annotations
