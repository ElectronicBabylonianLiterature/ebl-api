from typing import Tuple, List, Mapping, Callable
import attr
import pydash
from ebl.text.atf import Atf
from ebl.text.lemmatization import Lemmatization, LemmatizationError
from ebl.text.language import Language
from ebl.text.line import Line, ControlLine, EmptyLine, TextLine
from ebl.text.token import Token, Word, LanguageShift


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
        if self.lemmatization.is_compatible(lemmatization):
            zipped = pydash.zip_(self.lines, lemmatization.tokens)
            lines = tuple(
                pair[0].update_lemmatization(pair[1])
                for pair in zipped
            )
            return attr.evolve(
                self,
                lines=lines
            )
        else:
            raise LemmatizationError()

    def to_dict(self) -> dict:
        return {
            'lines': [line.to_dict() for line in self.lines]
        }

    @staticmethod
    def from_dict(data: dict):
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
            )
        }

        def create_tokens(content: List[dict]):
            return tuple(
                token_factories[token['type']](token)
                for token
                in content
            )
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
