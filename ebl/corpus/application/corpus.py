from abc import ABC, abstractmethod
from typing import List, Sequence, Tuple

from ebl.corpus.application.alignment_updater import AlignmentUpdater
from ebl.corpus.application.chapter_updater import ChapterUpdater
from ebl.corpus.application.lemmatization import ChapterLemmatization
from ebl.corpus.application.lemmatization_updater import LemmatizationUpdater
from ebl.corpus.application.lines_updater import LinesUpdater
from ebl.corpus.application.manuscripts_updater import ManuscriptUpdater
from ebl.corpus.application.text_hydrator import TextHydrator
from ebl.corpus.application.text_serializer import serialize
from ebl.corpus.application.text_validator import TextValidator
from ebl.corpus.domain.alignment import Alignment
from ebl.corpus.domain.chapter import Line
from ebl.corpus.domain.manuscript import Manuscript
from ebl.corpus.domain.parser import parse_chapter
from ebl.corpus.domain.text import Text, TextId, ChapterId
from ebl.corpus.domain.text_info import TextInfo
from ebl.fragmentarium.domain.museum_number import MuseumNumber
from ebl.transliteration.application.sign_repository import SignRepository
from ebl.transliteration.domain.transliteration_query import TransliterationQuery
from ebl.users.domain.user import User

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

    @abstractmethod
    def query_by_transliteration(self, query: TransliterationQuery) -> List[Text]:
        ...


def text_id_to_tuple(text: Text) -> Tuple[int, int]:
    return (text.id.category, text.id.index)


class Corpus:
    def __init__(
        self,
        repository: TextRepository,
        bibliography,
        changelog,
        transliteration_factory,
        sign_repository: SignRepository,
    ):
        self._repository: TextRepository = repository
        self._bibliography = bibliography
        self._changelog = changelog
        self._transliteration_factory = transliteration_factory
        self._sign_repository = sign_repository

    def create(self, text: Text, user) -> None:
        self._validate_text(text)
        self._repository.create(text)
        text_id = text_id_to_tuple(text)
        new_dict: dict = {**serialize(text), "_id": text_id}
        self._changelog.create(COLLECTION, user.profile, {"_id": text_id}, new_dict)

    def find(self, id_: TextId) -> Text:
        text = self._repository.find(id_)
        return self._hydrate_references(text)

    def search_transliteration(self, query: TransliterationQuery) -> List[TextInfo]:
        return (
            []
            if query.is_empty()
            else [
                TextInfo.of(text, query)
                for text in self._repository.query_by_transliteration(query)
            ]
        )

    def list(self) -> List[Text]:
        return self._repository.list()

    def update_alignment(
        self, id_: ChapterId, alignment: Alignment, user: User
    ) -> None:
        self._update_chapter(id_.text_id, AlignmentUpdater(id_.index, alignment), user)

    def update_manuscript_lemmatization(
        self, id_: ChapterId, lemmatization: ChapterLemmatization, user: User
    ) -> None:
        self._update_chapter(
            id_.text_id, LemmatizationUpdater(id_.index, lemmatization), user
        )

    def update_manuscripts(
        self,
        id_: ChapterId,
        manuscripts: Sequence[Manuscript],
        uncertain_fragments: Sequence[MuseumNumber],
        user: User,
    ) -> None:
        self._update_chapter(
            id_.text_id,
            ManuscriptUpdater(
                id_.index, manuscripts, uncertain_fragments, self._sign_repository
            ),
            user,
        )

    def import_lines(self, id_: ChapterId, atf: str, user: User) -> None:
        chapter = self._repository.find(id_.text_id).chapters[id_.index]
        lines = parse_chapter(atf, chapter.manuscripts)
        self.update_lines(id_, lines, user)

    def update_lines(self, id_: ChapterId, lines: Sequence[Line], user: User) -> None:
        self._update_chapter(
            id_.text_id, LinesUpdater(id_.index, lines, self._sign_repository), user
        )

    def _update_chapter(self, id_: TextId, updater: ChapterUpdater, user: User) -> None:
        old_text = self._repository.find(id_)
        updated_text = updater.update(old_text)
        self.update_text(id_, old_text, updated_text, user)

    def update_text(
        self, id_: TextId, old_text: Text, updated_text: Text, user: User
    ) -> None:
        self._validate_text(updated_text)
        self._create_changelog(old_text, updated_text, user)
        self._repository.update(id_, updated_text)

    def _validate_text(self, text: Text) -> None:
        TextValidator(self._bibliography, self._transliteration_factory).visit(text)

    def _hydrate_references(self, text: Text) -> Text:
        hydrator = TextHydrator(self._bibliography)
        hydrator.visit(text)
        return hydrator.text

    def _create_changelog(self, old_text, new_text, user) -> None:
        old_dict: dict = {**serialize(old_text), "_id": text_id_to_tuple(old_text)}
        new_dict: dict = {**serialize(new_text), "_id": text_id_to_tuple(new_text)}
        self._changelog.create(COLLECTION, user.profile, old_dict, new_dict)
