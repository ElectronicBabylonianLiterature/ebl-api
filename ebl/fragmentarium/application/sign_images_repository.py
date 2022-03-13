from abc import ABC, abstractmethod
from typing import Sequence

from ebl.fragmentarium.application.cropped_sign_image import CroppedSignImage, Base64


class SignImagesRepository(ABC):
    @abstractmethod
    def query_by_id(self, image_id: str) -> CroppedSignImage:
        ...

    @abstractmethod
    def create_or_update(self, cropped_sign_image: Sequence[CroppedSignImage]) -> None:
        ...
