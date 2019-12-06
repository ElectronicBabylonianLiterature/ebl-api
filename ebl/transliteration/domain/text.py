from typing import Iterable, Tuple

import attr
import pydash

from ebl.merger import Merger
from ebl.transliteration.domain.atf import (
    ATF_PARSER_VERSION,
    Atf,
    DEFAULT_ATF_PARSER_VERSION,
)
from ebl.transliteration.domain.lemmatization import (
    Lemmatization,
    LemmatizationError,
)
from ebl.transliteration.domain.line import Line
from ebl.transliteration.domain.line_schemas import dump_lines, load_lines
from ebl.transliteration.domain.word_tokens import Word


@attr.s(auto_attribs=True, frozen=True)
class Text:
    lines: Tuple[Line, ...] = tuple()
    parser_version: str = ATF_PARSER_VERSION

    @property
    def lemmatization(self) -> Lemmatization:
        return Lemmatization.from_list(
            [
                [
                    (
                        {"value": token.value, "uniqueLemma": list(token.unique_lemma),}
                        if isinstance(token, Word)
                        else {"value": token.value}
                    )
                    for token in line.content
                ]
                for line in self.lines
            ]
        )

    @property
    def atf(self) -> Atf:
        return Atf("\n".join(line.atf for line in self.lines))

    def update_lemmatization(self, lemmatization: Lemmatization) -> "Text":
        if len(self.lines) == len(lemmatization.tokens):
            zipped = pydash.zip_(list(self.lines), list(lemmatization.tokens))
            lines = tuple(
                line.update_lemmatization(lemmas) for [line, lemmas] in zipped
            )
            return attr.evolve(self, lines=lines)
        else:
            raise LemmatizationError()

    def merge(self, other: "Text") -> "Text":
        def map_(line: Line) -> str:
            return line.key

        def inner_merge(old: Line, new: Line) -> Line:
            return old.merge(new)

        merged_lines = Merger(map_, inner_merge).merge(self.lines, other.lines)
        return attr.evolve(
            self, lines=tuple(merged_lines), parser_version=other.parser_version,
        )

    def set_parser_version(self, parser_version: str) -> "Text":
        return attr.evolve(self, parser_version=parser_version)

    def to_dict(self) -> dict:
        return {
            "lines": dump_lines(self.lines),
            "parser_version": self.parser_version,
        }

    @staticmethod
    def from_dict(data: dict) -> "Text":
        lines = load_lines(data["lines"])
        return Text(lines, data.get("parser_version", DEFAULT_ATF_PARSER_VERSION))

    @staticmethod
    def of_iterable(
        lines: Iterable[Line], parser_version: str = ATF_PARSER_VERSION
    ) -> "Text":
        return Text(tuple(lines), parser_version)
