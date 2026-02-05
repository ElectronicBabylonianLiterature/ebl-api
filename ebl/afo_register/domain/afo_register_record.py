import attr
from typing import Sequence


@attr.s(frozen=True, auto_attribs=True)
class AfoRegisterRecord:
    afo_number: str = ""
    page: str = ""
    text: str = ""
    text_number: str = ""
    lines_discussed: str = ""
    discussed_by: str = ""
    discussed_by_notes: str = ""


@attr.s(frozen=True, auto_attribs=True)
class AfoRegisterRecordSuggestion:
    text: str = ""
    text_numbers: Sequence[str] = ()
