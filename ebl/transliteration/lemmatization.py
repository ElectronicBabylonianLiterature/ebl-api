from typing import List, Optional, Tuple

import attr
import pydash

from ebl.dictionary.word import WordId


class LemmatizationError(Exception):
    def __init__(self, message='Invalid lemmatization'):
        super().__init__(message)


@attr.s(auto_attribs=True, frozen=True)
class LemmatizationToken:
    value: str
    unique_lemma: Optional[Tuple[WordId, ...]] = None

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
