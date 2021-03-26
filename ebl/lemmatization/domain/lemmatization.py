from typing import Optional, Sequence

import attr

from ebl.dictionary.domain.word import WordId


class LemmatizationError(Exception):
    def __init__(self, message="Invalid lemmatization"):
        super().__init__(message)


@attr.s(auto_attribs=True, frozen=True)
class LemmatizationToken:
    value: str
    unique_lemma: Optional[Sequence[WordId]] = None


@attr.s(auto_attribs=True, frozen=True)
class Lemmatization:
    tokens: Sequence[Sequence[LemmatizationToken]] = tuple()
