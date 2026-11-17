from abc import ABC, abstractmethod
from typing import Optional

from ebl.corpus.domain.chapter import ChapterId


class ChapterCacheState(ABC):
    @abstractmethod
    def revision(self, chapter_key: str) -> Optional[str]:
        raise NotImplementedError

    @abstractmethod
    def content_revision(self, chapter_id: ChapterId) -> Optional[str]:
        raise NotImplementedError

    @abstractmethod
    def start_update(self, chapter_key: str) -> str:
        raise NotImplementedError

    @abstractmethod
    def finish_update(self, chapter_key: str, epoch: str) -> None:
        raise NotImplementedError
