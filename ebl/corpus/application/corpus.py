from abc import ABC, abstractmethod
from typing import List, Tuple

from ebl.corpus.application.alignment_updater import AlignmentUpdater
from ebl.corpus.application.chapter_updater import ChapterUpdater
from ebl.corpus.application.lines_updater import LinesUpdater
from ebl.corpus.application.manuscripts_updater import ManuscriptUpdater
from ebl.corpus.application.text_hydrator import TextHydrator
from ebl.corpus.application.text_serializer import serialize
from ebl.corpus.application.text_validator import TextValidator
from ebl.corpus.domain.text import Line, Manuscript, Text, TextId
from ebl.transliteration.domain.alignment import Alignment

COLLECTION = "texts"


class TextRepository(ABC):
    @abstractmethod
    def create(self, text: Text) -> None:
        ...

    @abstractmethod
    def find(self, id_: TextId) -> Text:
        ...

    @abstractmethod
    def list(self) -> List[Text]:
        ...

    @abstractmethod
    def update(self, id_: TextId, text: Text) -> None:
        ...


class Corpus:
    def __init__(
        self,
        repository: TextRepository,
        bibliography,
        changelog,
        transliteration_factory,
    ):
        self._repository: TextRepository = repository
        self._bibliography = bibliography
        self._changelog = changelog
        self._transliteration_factory = transliteration_factory

    def create(self, text: Text, user) -> None:
        self._validate_text(text)
        self._repository.create(text)
        new_dict: dict = {**serialize(text), "_id": text.id}
        self._changelog.create(COLLECTION, user.profile, {"_id": text.id}, new_dict)

    def find(self, id_: TextId) -> Text:
        text = self._repository.find(id_)
        return self._hydrate_references(text)

    def list(self) -> List[Text]:
        return self._repository.list()

    def update_alignment(
        self, id_: TextId, chapter_index: int, alignment: Alignment, user
    ):
        self._update_chapter(id_, AlignmentUpdater(chapter_index, alignment), user)

    def update_manuscripts(
        self,
        id_: TextId,
        chapter_index: int,
        manuscripts: Tuple[Manuscript, ...],
        user,
    ):
        self._update_chapter(id_, ManuscriptUpdater(chapter_index, manuscripts), user)

    def update_lines(
        self, id_: TextId, chapter_index: int, lines: Tuple[Line, ...], user
    ):
        self._update_chapter(id_, LinesUpdater(chapter_index, lines), user)

    def _update_chapter(self, id_: TextId, updater: ChapterUpdater, user):
        old_text = self._repository.find(id_)
        updated_text = updater.update(old_text)
        self._validate_text(updated_text)
        self._create_changelog(old_text, updated_text, user)
        self._repository.update(id_, updated_text)

    def _validate_text(self, text: Text) -> None:
        text.accept(TextValidator(self._bibliography, self._transliteration_factory))

    def _hydrate_references(self, text: Text) -> Text:
        hydrator = TextHydrator(self._bibliography)
        text.accept(hydrator)
        return hydrator.text

    def _create_changelog(self, old_text, new_text, user):
        old_dict: dict = {**serialize(old_text), "_id": old_text.id}
        new_dict: dict = {**serialize(new_text), "_id": new_text.id}
        self._changelog.create(COLLECTION, user.profile, old_dict, new_dict)
