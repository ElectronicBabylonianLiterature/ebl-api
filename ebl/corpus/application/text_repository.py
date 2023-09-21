from abc import ABC, abstractmethod
from typing import List, Optional, Sequence, Tuple
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
from ebl.common.query.query_result import CorpusQueryResult


class TextRepository(ABC):
    @abstractmethod
    def create(self, text: Text) -> None:
        ...

    @abstractmethod
    def create_chapter(
        self, chapter: Chapter, ngram_n: Optional[Sequence[int]] = None
    ) -> None:
        ...

    @abstractmethod
    def find(self, id_: TextId) -> Text:
        ...

    @abstractmethod
    def find_chapter(self, id_: ChapterId) -> Chapter:
        ...

    @abstractmethod
    def find_chapter_for_display(self, id_: ChapterId) -> ChapterDisplay:
        ...

    @abstractmethod
    def find_line(self, id_: ChapterId, number: int) -> Line:
        ...

    @abstractmethod
    def list(self) -> List[Text]:
        ...

    @abstractmethod
    def list_all_texts(self) -> Sequence:
        ...

    @abstractmethod
    def list_all_chapters(self) -> Sequence:
        ...

    @abstractmethod
    def update(self, id_: ChapterId, chapter: Chapter) -> None:
        ...

    @abstractmethod
    def query_by_transliteration(
        self, query: TransliterationQuery, pagination_index: int
    ) -> Tuple[Sequence[Chapter], int]:
        ...

    @abstractmethod
    def query_by_lemma(
        self, lemma: str, genre: Optional[Genre] = None
    ) -> Sequence[DictionaryLine]:
        ...

    @abstractmethod
    def query_manuscripts_by_chapter(self, id_: ChapterId) -> Sequence[Manuscript]:
        ...

    @abstractmethod
    def query_corpus_by_manuscript(
        self, museum_numbers: List[MuseumNumber]
    ) -> List[ManuscriptAttestation]:
        ...

    @abstractmethod
    def query_manuscripts_with_joins_by_chapter(
        self, id_: ChapterId
    ) -> Sequence[Manuscript]:
        ...

    @abstractmethod
    def query(self, query: dict) -> CorpusQueryResult:
        ...
