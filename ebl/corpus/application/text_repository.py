from abc import ABC, abstractmethod
from typing import List, Optional, Sequence, Tuple, TypedDict
from ebl.corpus.domain.text import Text, TextId
from ebl.corpus.domain.chapter_display import ChapterDisplay
from ebl.corpus.domain.chapter import Chapter, ChapterId
from ebl.transliteration.domain.genre import Genre
from ebl.corpus.domain.line import Line
from ebl.transliteration.domain.transliteration_query import TransliterationQuery
from ebl.corpus.domain.dictionary_line import DictionaryLine
from ebl.corpus.domain.manuscript import Manuscript
from ebl.transliteration.domain.museum_number import MuseumNumber
from ebl.corpus.domain.manuscript_attestation import ManuscriptAttestation
from ebl.corpus.domain.uncertain_fragment_attestation import (
    UncertainFragmentAttestation,
)
from ebl.common.query.query_result import CorpusQueryResult


class CorpusFragmentsMapping(TypedDict):
    manuscripts: List[ManuscriptAttestation]
    uncertain_fragments: List[UncertainFragmentAttestation]


class TextRepository(ABC):
    @abstractmethod
    def create(self, text: Text) -> None:
        raise NotImplementedError

    @abstractmethod
    def create_chapter(self, chapter: Chapter) -> None:
        raise NotImplementedError

    @abstractmethod
    def find(self, id_: TextId) -> Text:
        raise NotImplementedError

    @abstractmethod
    def find_chapter(self, id_: ChapterId) -> Chapter:
        raise NotImplementedError

    @abstractmethod
    def find_chapter_for_display(self, id_: ChapterId) -> ChapterDisplay:
        raise NotImplementedError

    @abstractmethod
    def find_line(self, id_: ChapterId, number: int) -> Line:
        raise NotImplementedError

    @abstractmethod
    def list(self) -> List[Text]:
        raise NotImplementedError

    @abstractmethod
    def list_all_texts(self) -> Sequence:
        raise NotImplementedError

    @abstractmethod
    def list_all_chapters(self) -> Sequence:
        raise NotImplementedError

    @abstractmethod
    def update(self, id_: ChapterId, chapter: Chapter) -> None:
        raise NotImplementedError

    @abstractmethod
    def query_by_transliteration(
        self, query: TransliterationQuery, pagination_index: int
    ) -> Tuple[Sequence[Chapter], int]:
        raise NotImplementedError

    @abstractmethod
    def query_by_lemma(
        self, lemma: str, genre: Optional[Genre] = None
    ) -> Sequence[DictionaryLine]:
        raise NotImplementedError

    @abstractmethod
    def query_manuscripts_by_chapter(self, id_: ChapterId) -> Sequence[Manuscript]:
        raise NotImplementedError

    @abstractmethod
    def query_corpus_by_manuscripts(
        self, museum_numbers: List[MuseumNumber]
    ) -> List[ManuscriptAttestation]:
        raise NotImplementedError

    @abstractmethod
    def query_corpus_by_uncertain_fragments(
        self, museum_numbers: List[MuseumNumber]
    ) -> List[UncertainFragmentAttestation]:
        raise NotImplementedError

    @abstractmethod
    def query_corpus_by_related_fragments(
        self, museum_numbers: List[MuseumNumber]
    ) -> CorpusFragmentsMapping:
        raise NotImplementedError

    @abstractmethod
    def query_manuscripts_with_joins_by_chapter(
        self, id_: ChapterId
    ) -> Sequence[Manuscript]:
        raise NotImplementedError

    @abstractmethod
    def query(self, query: dict) -> CorpusQueryResult:
        raise NotImplementedError

    @abstractmethod
    def get_sign_data(self, id_: ChapterId) -> dict:
        raise NotImplementedError

    @abstractmethod
    def get_all_sign_data(self) -> Sequence[dict]:
        raise NotImplementedError
