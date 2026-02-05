from enum import Enum, auto
from typing import Sequence

import attr


class AuthorRole(Enum):
    EDITOR = auto()
    REVISION = auto()


@attr.s(auto_attribs=True, frozen=True)
class Author:
    name: str
    prefix: str
    role: AuthorRole
    orcid_number: str


@attr.s(auto_attribs=True, frozen=True)
class Translator:
    name: str
    prefix: str
    orcid_number: str
    language: str


@attr.s(auto_attribs=True, frozen=True)
class Record:
    authors: Sequence[Author] = ()
    translators: Sequence[Translator] = ()
    publication_date: str = ""
