from abc import ABC, abstractmethod
from typing import List, Tuple

from ebl.corpus.alignment import Alignment
from ebl.corpus.alignment_updater import AlignmentUpdater
from ebl.corpus.chapter_updater import ChapterUpdater
from ebl.corpus.lines_updater import LinesUpdater
from ebl.corpus.manuscripts_updater import ManuscriptUpdater
from ebl.corpus.mongo_serializer import serialize
from ebl.corpus.text import Line, Manuscript, Text, TextId
from ebl.corpus.text_hydrator import TextHydrator
from ebl.corpus.text_validator import TextValidator

COLLECTION = 'texts'


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
    def __init__(self,
                 repository: TextRepository,
                 bibliography,
                 changelog,
                 sign_list):
        self._repository: TextRepository = repository
        self._bibliography = bibliography
        self._changelog = changelog
        self._sign_list = sign_list

    def create(self, text: Text, user) -> None:
        self._validate_text(text)
        self._repository.create(text)
        new_dict: dict = {**serialize(text), '_id': text.id}
        self._changelog.create(
            COLLECTION,
            user.profile,
            {'_id': text.id},
            new_dict
        )

    def find(self, id_: TextId) -> Text:
        text = self._repository.find(id_)
        return self._hydrate_references(text)

    def list(self) -> List[Text]:
        return self._repository.list()

    def update(self, id_: TextId, text: Text, user) -> None:
        old_text = self._repository.find(id_)
        self._update(id_, old_text, text, user)

    def update_alignment(self,
                         id_: TextId,
                         chapter_index: int,
                         alignment: Alignment,
                         user):
        self._update_chapter(id_,
                             AlignmentUpdater(chapter_index, alignment),
                             user)

    def update_manuscripts(self,
                           id_: TextId,
                           chapter_index: int,
                           manuscripts: Tuple[Manuscript, ...],
                           user):
        self._update_chapter(id_,
                             ManuscriptUpdater(chapter_index, manuscripts),
                             user)

    def update_lines(self,
                     id_: TextId,
                     chapter_index: int,
                     lines: Tuple[Line, ...],
                     user):
        self._update_chapter(id_, LinesUpdater(chapter_index, lines), user)

    def _update_chapter(self,
                        id_: TextId,
                        updater: ChapterUpdater,
                        user):
        old_text = self._repository.find(id_)
        updated_text = updater.update(old_text)
        self._update(id_, old_text, updated_text, user)

    def _validate_text(self, text: Text) -> None:
        text.accept(TextValidator(self._bibliography, self._sign_list))

    def _hydrate_references(self, text: Text) -> Text:
        hydrator = TextHydrator(self._bibliography)
        text.accept(hydrator)
        return hydrator.text

    def _create_changelog(self, old_text, new_text, user):
        old_dict: dict = {**serialize(old_text), '_id': old_text.id}
        new_dict: dict = {**serialize(new_text), '_id': new_text.id}
        self._changelog.create(
            COLLECTION,
            user.profile,
            old_dict,
            new_dict
        )

    def _update(self, id_, old_text, text, user):
        self._validate_text(text)
        self._create_changelog(old_text, text, user)
        self._repository.update(id_, text)
