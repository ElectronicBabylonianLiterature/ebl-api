import json
import re
from typing import Callable, Generic, Optional, Sequence, TypeVar

import attr
from falcon import testing

from ebl.corpus.application.chapter_edit_writer import ChapterEditWriter, SavedChapter
from ebl.corpus.application.chapter_updater import ChapterUpdater
from ebl.corpus.application.corpus import Corpus
from ebl.corpus.domain.chapter import Chapter, ChapterId
from ebl.corpus.domain.line import Line
from ebl.tests.corpus.chapter_edit_support import ChapterEditRequest, post_edit
from ebl.tests.corpus.line_annotation_support import replace_item

A = TypeVar("A")
ChapterUpdate = Callable[[Chapter], Chapter]
ANNOTATION_QUERY = "view=outline&revision=legacy"


def create_count_error(subject: str, got: int, expected: int) -> str:
    return re.escape(f"Invalid number of {subject}. Got {got}, expected {expected}.")


def matches(pattern: Optional[str], message: Optional[str]) -> bool:
    return (
        message is None
        if pattern is None
        else message is not None
        and re.fullmatch(pattern, message, re.DOTALL) is not None
    )


@attr.s(frozen=True, auto_attribs=True)
class InvalidCase(Generic[A]):
    name: str
    change: Callable[[A], A]
    line_error: str
    chapter_error: Optional[str]
    index: int = 0


@attr.s(frozen=True, auto_attribs=True)
class InvalidAnnotation:
    name: str
    update_line: ChapterUpdate
    update_chapter: ChapterUpdate
    create_request: Callable[[Chapter], ChapterEditRequest]
    line_error: str
    chapter_error: Optional[str]


@attr.s(frozen=True, auto_attribs=True)
class AnnotationKind(Generic[A]):
    name: str
    find: Callable[[Line], A]
    create_new: Callable[[Line], A]
    dump: Callable[[A], Sequence[object]]
    create_line_updater: Callable[[int, A], ChapterUpdater]
    create_chapter_updater: Callable[[Sequence[A]], ChapterUpdater]
    save: Callable[[ChapterEditWriter, ChapterId, int, A], SavedChapter]
    save_all: Callable[[Corpus, ChapterId, Sequence[A]], Chapter]

    def create_request(self, index: object, annotation: object) -> ChapterEditRequest:
        return ChapterEditRequest(
            f"/lines/{index}/{self.name}", json.dumps({self.name: annotation})
        )

    def dump_new(self, line: Line) -> Sequence[object]:
        return self.dump(self.create_new(line))

    def create_new_request(self, chapter: Chapter, index: int) -> ChapterEditRequest:
        return self.create_request(index, self.dump_new(chapter.lines[index]))

    def create_stored_request(self, chapter: Chapter, index: int) -> ChapterEditRequest:
        return self.create_request(index, self.dump(self.find(chapter.lines[index])))

    def post_new(
        self,
        client: testing.TestClient,
        chapter: Chapter,
        index: int,
        query_string: str = ANNOTATION_QUERY,
    ) -> testing.Result:
        return post_edit(
            client, chapter, self.create_new_request(chapter, index), query_string
        )

    def _replace(self, chapter: Chapter, index: int, annotation: A) -> Sequence[A]:
        return replace_item(
            [self.find(line) for line in chapter.lines], index, annotation
        )

    def update_line(self, chapter: Chapter, index: int) -> Chapter:
        return self.create_line_updater(
            index, self.create_new(chapter.lines[index])
        ).update(chapter)

    def update_chapter(self, chapter: Chapter, index: int) -> Chapter:
        return self.create_chapter_updater(
            self._replace(chapter, index, self.create_new(chapter.lines[index]))
        ).update(chapter)

    def save_line(
        self, writer: ChapterEditWriter, chapter: Chapter, index: int
    ) -> SavedChapter:
        return self.save(
            writer, chapter.id_, index, self.create_new(chapter.lines[index])
        )

    def save_chapter(self, corpus: Corpus, sibling: Chapter, index: int) -> Chapter:
        return self.save_all(
            corpus,
            sibling.id_,
            self._replace(sibling, index, self.create_new(sibling.lines[index])),
        )

    def create_invalid(self, case: InvalidCase[A]) -> InvalidAnnotation:
        def create(chapter: Chapter) -> A:
            return case.change(self.create_new(chapter.lines[case.index]))

        return InvalidAnnotation(
            f"{self.name}: {case.name}",
            lambda chapter: self.create_line_updater(
                case.index, create(chapter)
            ).update(chapter),
            lambda chapter: self.create_chapter_updater(
                self._replace(chapter, case.index, create(chapter))
            ).update(chapter),
            lambda chapter: self.create_request(case.index, self.dump(create(chapter))),
            case.line_error,
            case.chapter_error,
        )
