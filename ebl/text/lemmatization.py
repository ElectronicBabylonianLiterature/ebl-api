from typing import Optional, Tuple, List
import attr
import pydash
from ebl.merger import Merger
from ebl.fragmentarium.transliteration import Transliteration


class LemmatizationError(Exception):
    def __init__(self):
        super().__init__('Invalid lemmatization')


@attr.s(auto_attribs=True, frozen=True)
class LemmatizationToken:
    value: str
    unique_lemma: Optional[Tuple[str, ...]] = None

    def to_dict(self) -> dict:
        return pydash.map_keys(
            attr.asdict(self, filter=lambda _, value: value is not None),
            lambda _, key: pydash.strings.camel_case(key)
        )

    @staticmethod
    def from_dict(data: dict):
        return (
            LemmatizationToken(data['value'], tuple(data['uniqueLemma']))
            if 'uniqueLemma' in data
            else LemmatizationToken(data['value'])
        )


@attr.s(auto_attribs=True, frozen=True)
class Lemmatization:
    tokens: Tuple[Tuple[LemmatizationToken, ...], ...] = tuple()

    @property
    def atf(self) -> str:
        return '\n'.join([
            ' '.join([token.value for token in line])
            for line in self.tokens
        ])

    def merge(self, transliteration: Transliteration) -> 'Lemmatization':
        merged_tokens = Merger(lambda token: token.value, 2).merge(
            self.tokens,
            self._tokenize(transliteration)
        )

        return Lemmatization(tuple(
            tuple(line)
            for line in merged_tokens
        ))

    @staticmethod
    def of_transliteration(
            transliteration: Transliteration
    ) -> 'Lemmatization':
        tokens = Lemmatization._tokenize(transliteration)
        return Lemmatization(tokens)

    @staticmethod
    def _tokenize(
            transliteration: Transliteration
    ) -> Tuple[Tuple[LemmatizationToken, ...], ...]:
        tokens = transliteration.tokenize(
            lambda value: LemmatizationToken(value, tuple())
        )
        return tuple(tuple(line) for line in tokens)

    def is_compatible(self, other: 'Lemmatization') -> bool:
        def to_values(tokens):
            return [
                [
                    token.value
                    for token in line
                ] for line in tokens
            ]

        return to_values(self.tokens) == to_values(other.tokens)

    def to_list(self) -> List[List[dict]]:
        return [
            [token.to_dict() for token in line]
            for line in self.tokens
        ]

    @staticmethod
    def from_list(data: List[List[dict]]) -> 'Lemmatization':
        return Lemmatization(
            tuple(
                tuple(
                    LemmatizationToken.from_dict(token)
                    for token in line
                )
                for line in data
            )
        )
