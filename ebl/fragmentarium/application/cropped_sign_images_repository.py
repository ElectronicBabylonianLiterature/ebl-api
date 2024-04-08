from abc import ABC, abstractmethod
from typing import Sequence

from ebl.fragmentarium.application.cropped_sign_image import CroppedSignImage


class CroppedSignImagesRepository(ABC):
    @abstractmethod
    def query_by_id(self, image_id: str) -> CroppedSignImage: ...

    @abstractmethod
    def create_many(self, cropped_sign_images: Sequence[CroppedSignImage]) -> None: ...
