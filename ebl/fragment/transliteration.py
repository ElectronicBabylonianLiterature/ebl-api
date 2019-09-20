from typing import Optional

import attr

from ebl.text.atf import Atf
from ebl.text.atf_parser import parse_atf
from ebl.text.text import Text


@attr.s(auto_attribs=True, frozen=True)
class Transliteration:
    atf: Atf = Atf('')
    notes: str = ''
    signs: Optional[str] = None

    def parse(self) -> Text:
        return parse_atf(self.atf)
