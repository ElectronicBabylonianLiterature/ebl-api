from abc import ABC, abstractmethod
from typing import Optional

from ebl.iiif.domain.resources import ImageService

LEVEL_TWO = "level2"


class ImageServiceLocator(ABC):
    @abstractmethod
    def service_for(self, media_id: str) -> Optional[ImageService]:
        raise NotImplementedError


class NoImageService(ImageServiceLocator):
    def service_for(self, media_id: str) -> Optional[ImageService]:
        return None
