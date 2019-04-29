from typing import Callable, Iterable, List, Mapping, Tuple

import attr
import pydash

from ebl.merger import Merger
from ebl.text.atf import Atf
from ebl.text.language import Language
from ebl.text.lemmatization import Lemmatization, LemmatizationError
from ebl.text.line import ControlLine, EmptyLine, Line, TextLine
from ebl.text.token import (DocumentOrientedGloss, LanguageShift,
                            LoneDeterminative, Partial, Token, Word,
                            LineContinuation)


def create_tokens(content: List[dict]) -> Tuple[Token, ...]:
    token_factories: Mapping[str, Callable[[dict], Token]] = {
        'Token': lambda data: Token(
            data['value']
        ),
        'Word': lambda data: Word(
            data['value'],
            Language[data['language']],
            data['normalized'],
            tuple(data['uniqueLemma']),
        ),
        'LanguageShift': lambda data: LanguageShift(
            data['value']
        ),
        'LoneDeterminative': lambda data: LoneDeterminative(
            data['value'],
            Language[data['language']],
            data['normalized'],
            tuple(data['uniqueLemma']),
            Partial(*data['partial'])
        ),
        'DocumentOrientedGloss': lambda data: DocumentOrientedGloss(
            data['value']
        ),
        'LineContinuation': lambda data: LineContinuation(data['value'])
    }

    return tuple(
        token_factories[token['type']](token)
        for token
        in content
    )


@attr.s(auto_attribs=True, frozen=True)
class Text:
    lines: Tuple[Line, ...] = tuple()

    @property
    def lemmatization(self) -> Lemmatization:
        return Lemmatization.from_list([
            [
                (
                    {
                        'value': token.value,
                        'uniqueLemma': list(token.unique_lemma)
                    }
                    if isinstance(token, Word)
                    else {'value': token.value}
                )
                for token in line.content
            ]
            for line in self.lines
        ])

    @property
    def atf(self) -> Atf:
        return Atf('\n'.join(line.atf for line in self.lines))

    def update_lemmatization(self, lemmatization: Lemmatization) -> 'Text':
        if len(self.lines) == len(lemmatization.tokens):
            zipped = pydash.zip_(list(self.lines), list(lemmatization.tokens))
            lines = tuple(
                line.update_lemmatization(lemmas)
                for [line, lemmas] in zipped
            )
            return attr.evolve(
                self,
                lines=lines
            )
        else:
            raise LemmatizationError()

    def merge(self, other: 'Text') -> 'Text':
        def map_(line: Line) -> str:
            return line.atf

        def inner_merge(old: Line, new: Line) -> Line:
            return old.merge(new)

        merged_lines = Merger(
            map_,
            inner_merge
        ).merge(
            self.lines, other.lines
        )
        return attr.evolve(self, lines=tuple(merged_lines))

    def to_dict(self) -> dict:
        return {
            'lines': [line.to_dict() for line in self.lines]
        }

    @staticmethod
    def from_dict(data: dict) -> 'Text':
        line_factories: Mapping[str, Callable[[str, List[dict]], Line]] = {
            'ControlLine':
                lambda prefix, content: ControlLine(
                    prefix, create_tokens(content)
                ),
            'TextLine':
                lambda prefix, content: TextLine(
                    prefix, create_tokens(content)
                ),
            'EmptyLine':
                lambda _prefix, _content: EmptyLine()
        }
        lines = tuple(
            line_factories[line['type']](line['prefix'], line['content'])
            for line
            in data['lines']
        )
        return Text(lines)

    @staticmethod
    def of_iterable(lines: Iterable[Line]) -> 'Text':
        return Text(tuple(lines))
