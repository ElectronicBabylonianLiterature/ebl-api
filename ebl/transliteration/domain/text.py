from itertools import count, zip_longest
from collections import defaultdict
from typing import (
    Callable,
    DefaultDict,
    Dict,
    Iterable,
    List,
    Mapping,
    Sequence,
    Tuple,
    Type,
    Iterator,
    cast,
)

import attr

from ebl.fragmentarium.domain.named_entity import (
    AnnotationSpan,
    EntityAnnotationSpan,
    RealiaAnnotationSpan,
)
from ebl.fragmentarium.domain.token_annotation import LineIndex, TextLemmaAnnotation
from ebl.lemmatization.domain.lemmatization import Lemmatization, LemmatizationError
from ebl.merger import Merger
from ebl.transliteration.domain.at_line import (
    ColumnAtLine,
    ObjectAtLine,
    SurfaceAtLine,
    SealAtLine,
)
from ebl.transliteration.domain.labels_validator import _validate_extents
from ebl.transliteration.domain.translation_line import TranslationLine
from ebl.transliteration.domain.tokens import Token
from ebl.transliteration.domain.atf import ATF_PARSER_VERSION, Atf
from ebl.transliteration.domain.line import Line
from ebl.transliteration.domain.line_label import LineLabel
from ebl.transliteration.domain.text_line import TextLine
from ebl.transliteration.domain.word_tokens import AbstractWord

__all__ = ["LineLabel", "Text", "TextLine", "TranslationLine", "set_id"]


def _map_spans_by_token(spans: Sequence[AnnotationSpan]) -> Dict[str, List[str]]:
    token_map: DefaultDict[str, List[str]] = defaultdict(list)
    for span in spans:
        for token_id in span.span:
            token_map[token_id].append(span.id)
    return token_map


def set_id(token: Token, count: Iterator[int]) -> Token:
    return (
        token.set_id(f"Word-{next(count)}")
        if (isinstance(token, AbstractWord) and token.id_ is None)
        else token
    )


@attr.s(auto_attribs=True, frozen=True)
class Text:
    lines: Sequence[Line] = attr.ib(default=(), validator=_validate_extents)
    parser_version: str = ATF_PARSER_VERSION

    @property
    def number_of_lines(self) -> int:
        return len(self.text_lines)

    @property
    def text_lines(self) -> Sequence[TextLine]:
        return tuple(line for line in self.lines if isinstance(line, TextLine))

    @property
    def lemmatization(self) -> Lemmatization:
        return Lemmatization(tuple(line.lemmatization for line in self.lines))

    @property
    def atf(self) -> Atf:
        return Atf("\n".join(line.atf for line in self.lines))

    @property
    def labels(self) -> Sequence[LineLabel]:
        current: LineLabel = LineLabel(None, None, None, None, None)
        labels: List[LineLabel] = []

        handlers: Mapping[
            Type[Line], Callable[[Line], Tuple[LineLabel, List[LineLabel]]]
        ] = {
            TextLine: lambda line: (
                current,
                [
                    *labels,
                    current.set_line_number(cast(TextLine, line).line_number),
                ],
            ),
            ColumnAtLine: lambda line: (
                current.set_column(cast(ColumnAtLine, line).column_label),
                labels,
            ),
            SurfaceAtLine: lambda line: (
                current.set_surface(cast(SurfaceAtLine, line).surface_label),
                labels,
            ),
            ObjectAtLine: lambda line: (
                current.set_object(cast(ObjectAtLine, line).label),
                labels,
            ),
            SealAtLine: lambda line: (
                current.set_seal(cast(SealAtLine, line).number),
                labels,
            ),
        }

        for index, line in enumerate(self.lines):
            if type(line) in handlers:
                current = current.set_line_index(index)
                current, labels = handlers[type(line)](line)
        return labels

    @property
    def is_empty(self) -> bool:
        return len(self.lines) == 0

    def update_lemmatization(self, lemmatization: Lemmatization) -> "Text":
        if len(self.lines) == len(lemmatization.tokens):
            zipped = zip_longest(self.lines, lemmatization.tokens)
            lines = tuple(
                line.update_lemmatization(lemmas) for [line, lemmas] in zipped
            )
            return attr.evolve(self, lines=lines)
        else:
            raise LemmatizationError()

    def update_lemma_annotation(self, annotation: TextLemmaAnnotation) -> "Text":
        lines = tuple(
            (
                line.update_lemma_annotation(annotation[LineIndex(index)])
                if LineIndex(index) in annotation
                else line
            )
            for index, line in enumerate(self.lines)
        )
        return attr.evolve(self, lines=lines)

    def merge(self, other: "Text") -> "Text":
        def map_(line: Line) -> str:
            return line.key

        def inner_merge(old: Line, new: Line) -> Line:
            return old.merge(new)

        merged_lines = Merger(map_, inner_merge).merge(self.lines, other.lines)
        return attr.evolve(
            self, lines=tuple(merged_lines), parser_version=other.parser_version
        )

    def set_parser_version(self, parser_version: str) -> "Text":
        return attr.evolve(self, parser_version=parser_version)

    def _get_max_token_id(self) -> int:
        return max(
            (
                int(token.id_.split("-")[1]) if token.id_ else 0
                for line in self.text_lines
                for token in line.content
                if isinstance(token, AbstractWord)
            ),
            default=0,
        )

    def set_token_ids(self) -> "Text":
        word_id = count(self._get_max_token_id() + 1)

        def set_word_ids(line: Line) -> Line:
            return (
                attr.evolve(
                    line,
                    content=tuple(set_id(token, word_id) for token in line.content),
                )
                if isinstance(line, TextLine)
                else line
            )

        return attr.evolve(self, lines=tuple(set_word_ids(line) for line in self.lines))

    @staticmethod
    def of_iterable(
        lines: Iterable[Line], parser_version: str = ATF_PARSER_VERSION
    ) -> "Text":
        return Text(tuple(lines), parser_version)

    def set_named_entities(
        self,
        entity_spans: Sequence[EntityAnnotationSpan],
        realia_spans: Sequence[RealiaAnnotationSpan],
    ) -> "Text":
        token_entity_map = _map_spans_by_token(entity_spans)
        token_realia_map = _map_spans_by_token(realia_spans)

        return attr.evolve(
            self,
            lines=tuple(
                (
                    line.set_named_entities(token_entity_map, token_realia_map)
                    if isinstance(line, TextLine)
                    else line
                )
                for line in self.lines
            ),
        )
