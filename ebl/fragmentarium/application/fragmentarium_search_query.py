import attr

from ebl.transliteration.application.transliteration_query_factory import (
    TransliterationQueryFactory,
)
from ebl.transliteration.domain.transliteration_query import TransliterationQuery


@attr.attrs(auto_attribs=True, frozen=True)
class FragmentariumSearchQuery:
    number: str = attr.ib(converter=str, default="")
    transliteration: TransliterationQuery = attr.ib(
        factory=TransliterationQueryFactory.create_empty
    )
    bibliography_id: str = ""
    pages: str = ""
