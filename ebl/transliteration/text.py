from typing import Callable, Iterable, List, Mapping, Tuple

import attr
import pydash

from ebl.atf.atf import ATF_PARSER_VERSION, Atf, DEFAULT_ATF_PARSER_VERSION
from ebl.merger import Merger
from ebl.transliteration.language import Language
from ebl.transliteration.lemmatization import Lemmatization, LemmatizationError
from ebl.transliteration.line import ControlLine, EmptyLine, Line, TextLine
from ebl.transliteration.token import (BrokenAway, DocumentOrientedGloss,
                                       Erasure,
                                       ErasureState, LanguageShift,
                                       LineContinuation,
                                       LoneDeterminative, OmissionOrRemoval,
                                       Partial,
                                       PerhapsBrokenAway, Side, Token, Word)


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
            ErasureState[data.get('erasure', ErasureState.NONE.name)],
            data.get('alignment')
        ),
        'LanguageShift': lambda data: LanguageShift(
            data['value']
        ),
        'LoneDeterminative': lambda data: LoneDeterminative(
            data['value'],
            Language[data['language']],
            data['normalized'],
            tuple(data['uniqueLemma']),
            ErasureState[data.get('erasure', ErasureState.NONE.name)],
            data.get('alignment'),
            Partial(*data['partial'])
        ),
        'DocumentOrientedGloss': lambda data: DocumentOrientedGloss(
            data['value']
        ),
        'BrokenAway': lambda data: BrokenAway(
            data['value']
        ),
        'PerhapsBrokenAway': lambda data: PerhapsBrokenAway(
            data['value']
        ),
        'OmissionOrRemoval': lambda data: OmissionOrRemoval(
            data['value']
        ),
        'LineContinuation': lambda data: LineContinuation(data['value']),
        'Erasure': lambda data: Erasure(data['value'],
                                        Side[data['side']])
    }

    return tuple(
        token_factories[token['type']](token)
        for token
        in content
    )


@attr.s(auto_attribs=True, frozen=True)
class Text:
    lines: Tuple[Line, ...] = tuple()
    parser_version: str = ATF_PARSER_VERSION

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
            types = [token.to_dict()['type'] for token in line.content]
            return '⋮'.join([line.atf] + types)

        def inner_merge(old: Line, new: Line) -> Line:
            return old.merge(new)

        merged_lines = Merger(
            map_, inner_merge
        ).merge(
            self.lines, other.lines
        )
        return attr.evolve(self,
                           lines=tuple(merged_lines),
                           parser_version=other.parser_version)

    def set_parser_version(self, parser_version: str) -> 'Text':
        return attr.evolve(self, parser_version=parser_version)

    def to_dict(self) -> dict:
        return {
            'lines': [line.to_dict() for line in self.lines],
            'parser_version': self.parser_version
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
        return Text(lines, data.get('parser_version',
                                    DEFAULT_ATF_PARSER_VERSION))

    @staticmethod
    def of_iterable(lines: Iterable[Line],
                    parser_version: str = ATF_PARSER_VERSION) -> 'Text':
        return Text(tuple(lines), parser_version)
