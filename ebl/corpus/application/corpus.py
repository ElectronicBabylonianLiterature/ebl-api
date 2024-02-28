from typing import List, Optional, Sequence, Tuple
import attr
from ebl.common.query.query_result import CorpusQueryResult
from ebl.corpus.application.text_repository import TextRepository
from ebl.corpus.application.alignment_updater import AlignmentUpdater
from ebl.corpus.application.manuscript_reference_injector import (
    ManuscriptReferenceInjector,
)
from ebl.corpus.application.chapter_updater import ChapterUpdater
from ebl.corpus.application.lemmatization import ChapterLemmatization
from ebl.corpus.application.lemmatization_updater import LemmatizationUpdater
from ebl.corpus.application.lines_updater import LinesUpdater
from ebl.corpus.application.manuscripts_updater import ManuscriptUpdater
from ebl.corpus.application.schemas import ChapterSchema
from ebl.corpus.application.text_validator import TextValidator
from ebl.corpus.domain.alignment import Alignment
from ebl.corpus.domain.chapter import Chapter, ChapterId
from ebl.corpus.domain.chapter_display import ChapterDisplay
from ebl.corpus.domain.chapter_info import ChapterInfo, ChapterInfosPagination
from ebl.corpus.domain.dictionary_line import DictionaryLine
from ebl.corpus.domain.line import Line
from ebl.corpus.domain.lines_update import LinesUpdate
from ebl.corpus.domain.manuscript import Manuscript
from ebl.corpus.domain.parser import parse_chapter
from ebl.corpus.domain.text import Text, TextId
from ebl.errors import DataError, Defect, NotFoundError
from ebl.transliteration.application.parallel_line_injector import ParallelLineInjector
from ebl.transliteration.domain.genre import Genre
from ebl.transliteration.domain.museum_number import MuseumNumber
from ebl.corpus.domain.manuscript_attestation import ManuscriptAttestation
from ebl.transliteration.application.sign_repository import SignRepository
from ebl.transliteration.domain.transliteration_query import TransliterationQuery
from ebl.users.domain.user import User


COLLECTION = "chapters"


class Corpus:
    def __init__(
        self,
        repository: TextRepository,
        bibliography,
        changelog,
        sign_repository: SignRepository,
        parallel_injector: ParallelLineInjector,
    ):
        self._repository: TextRepository = repository
        self._bibliography = bibliography
        self._changelog = changelog
        self._sign_repository = sign_repository
        self._parallel_injector = parallel_injector

    def find(self, id_: TextId) -> Text:
        return self._repository.find(id_)

    def find_chapter(self, id_: ChapterId) -> Chapter:
        chapter = self._repository.find_chapter(id_)
        return self._inject_references(chapter)

    def find_chapter_for_display(self, id_: ChapterId) -> ChapterDisplay:
        return self._inject_parallels(self._repository.find_chapter_for_display(id_))

    def find_line(
        self, id_: ChapterId, number: int
    ) -> Tuple[Line, Sequence[Manuscript]]:
        return self._repository.find_line(id_, number), self.find_manuscripts(id_)

    def find_line_with_manuscript_joins(
        self, id_: ChapterId, number: int
    ) -> Tuple[Line, Sequence[Manuscript]]:
        return self._repository.find_line(
            id_, number
        ), self.find_manuscripts_with_joins(id_)

    def find_manuscripts(self, id_: ChapterId) -> Sequence[Manuscript]:
        return self._inject_references_to_manuscripts(
            self._repository.query_manuscripts_by_chapter(id_)
        )

    def find_manuscripts_with_joins(self, id_: ChapterId) -> Sequence[Manuscript]:
        return self._inject_references_to_manuscripts(
            self._repository.query_manuscripts_with_joins_by_chapter(id_)
        )

    def search_corpus_by_manuscript(
        self, museum_numbers: List[MuseumNumber]
    ) -> List[ManuscriptAttestation]:
        return self._repository.query_corpus_by_manuscript(museum_numbers)

    def _inject_references_to_manuscripts(
        self, manuscripts: Sequence[Manuscript]
    ) -> Sequence[Manuscript]:
        injector = ManuscriptReferenceInjector(self._bibliography)
        try:
            return tuple(map(injector.inject_manuscript, manuscripts))
        except NotFoundError as error:
            raise Defect(error) from error

    def search_transliteration(
        self, query: TransliterationQuery, pagination_index: int
    ) -> ChapterInfosPagination:
        if query.is_empty():
            return ChapterInfosPagination([], 0)
        chapters, total_count = self._repository.query_by_transliteration(
            query, pagination_index
        )
        return ChapterInfosPagination(
            [ChapterInfo.of(chapter, query) for chapter in chapters], total_count
        )

    def search_lemma(
        self, query: str, genre: Optional[Genre] = None
    ) -> Sequence[DictionaryLine]:
        return tuple(
            attr.evolve(
                line,
                manuscripts=self._inject_references_to_manuscripts(line.manuscripts),
            )
            for line in self._repository.query_by_lemma(query, genre)
        )

    def query(self, query: dict) -> CorpusQueryResult:
        return self._repository.query(query)

    def list(self) -> List[Text]:
        return self._repository.list()

    def list_all_texts(self) -> Sequence:
        return self._repository.list_all_texts()

    def list_all_chapters(self) -> Sequence:
        return self._repository.list_all_chapters()

    def update_alignment(
        self, id_: ChapterId, alignment: Alignment, user: User
    ) -> Chapter:
        return self._update_chapter(id_, AlignmentUpdater(alignment), user)

    def get_sign_data(self, id_: ChapterId) -> dict:
        return self._repository.get_sign_data(id_)

    def update_manuscript_lemmatization(
        self, id_: ChapterId, lemmatization: ChapterLemmatization, user: User
    ) -> Chapter:
        return self._update_chapter(id_, LemmatizationUpdater(lemmatization), user)

    def update_manuscripts(
        self,
        id_: ChapterId,
        manuscripts: Sequence[Manuscript],
        uncertain_fragments: Sequence[MuseumNumber],
        user: User,
    ) -> Chapter:
        try:
            injector = ManuscriptReferenceInjector(self._bibliography)
            manuscripts = tuple(
                injector.inject_manuscript(manuscript) for manuscript in manuscripts
            )
        except NotFoundError as error:
            raise DataError(error) from error

        return self._update_chapter(
            id_,
            ManuscriptUpdater(manuscripts, uncertain_fragments, self._sign_repository),
            user,
        )

    def import_lines(self, id_: ChapterId, atf: str, user: User) -> Chapter:
        chapter = self.find_chapter(id_)
        lines = parse_chapter(atf, chapter.manuscripts)
        return self.update_lines(id_, LinesUpdate(lines, set(), {}), user)

    def update_lines(self, id_: ChapterId, lines: LinesUpdate, user: User) -> Chapter:
        return self._update_chapter(
            id_, LinesUpdater(lines, self._sign_repository), user
        )

    def _update_chapter(
        self, id_: ChapterId, updater: ChapterUpdater, user: User
    ) -> Chapter:
        old_chapter = self.find_chapter(id_)
        updated_chapter = updater.update(old_chapter)
        self.update_chapter(id_, old_chapter, updated_chapter, user)
        return updated_chapter

    def update_chapter(
        self, id_: ChapterId, old: Chapter, updated: Chapter, user: User
    ) -> None:
        self._validate_chapter(updated)
        self._create_changelog(old, updated, user)
        self._repository.update(id_, updated)

    def _validate_chapter(self, chapter: Chapter) -> None:
        TextValidator().visit(chapter)

    def _inject_references(self, chapter: Chapter) -> Chapter:
        try:
            injector = ManuscriptReferenceInjector(self._bibliography)
            injector.visit(chapter)
            return injector.chapter
        except NotFoundError as error:
            raise Defect(error) from error

    def _create_changelog(self, old: Chapter, new: Chapter, user: User) -> None:
        old_dict: dict = {**ChapterSchema().dump(old), "_id": old.id_.to_tuple()}
        new_dict: dict = {**ChapterSchema().dump(new), "_id": new.id_.to_tuple()}
        self._changelog.create(COLLECTION, user.profile, old_dict, new_dict)

    def _inject_parallels(self, chapter: ChapterDisplay) -> ChapterDisplay:
        return attr.evolve(
            chapter,
            lines=tuple(
                attr.evolve(
                    line,
                    variants=tuple(
                        attr.evolve(
                            variant,
                            parallel_lines=self._parallel_injector.inject(
                                variant.parallel_lines
                            ),
                        )
                        for variant in line.variants
                    ),
                )
                for line in chapter.lines
            ),
        )
