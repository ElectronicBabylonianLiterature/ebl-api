from enum import Enum
import re

import attr


@attr.s(auto_attribs=True, frozen=True)
class ScopeItem(Enum):
    def __init__(self, scope_string: str):
        match = re.match("([^:]+):(.+)(:?-(.+))?", scope_string)

        if not match:
            raise ValueError(f"Unexepcted scope format: {scope_string!r}")

        self.prefix = match[1]
        self.name = match[2]
        self.suffix = match[3] if len(match.groups()) > 3 else ""

    def __str__(self):
        suffix = f"-{self.suffix}" if self.suffix else ""
        return f"{self.prefix}:{self.name}{suffix}"


@attr.s(auto_attribs=True, frozen=True)
class Scope(ScopeItem):
    READ_CAIC_FRAGMENTS = "read:CAIC-fragments"
    READ_ITALIANNINEVEH_FRAGMENTS = "read:ITALIANNINEVEH-fragments"
    READ_SIPPARLIBRARY_FRAGMENTS = "read:SIPPARLIBRARY-fragments"
    READ_URUKLBU_FRAGMENTS = "read:URUKLBU-fragments"
    READ_AKG_FOLIOS = "read:AKG-folios"
    READ_ARG_FOLIOS = "read:ARG-folios"
    READ_CB_FOLIOS = "read:CB-folios"
    READ_EL_FOLIOS = "read:EL-folios"
    READ_ER_FOLIOS = "read:ER-folios"
    READ_EVW_FOLIOS = "read:EVW-folios"
    READ_FWG_FOLIOS = "read:FWG-folios"
    READ_GS_FOLIOS = "read:GS-folios"
    READ_ILF_FOLIOS = "read:ILF-folios"
    READ_JS_FOLIOS = "read:JS-folios"
    READ_MJG_FOLIOS = "read:MJG-folios"
    READ_RB_FOLIOS = "read:RB-folios"
    READ_SJL_FOLIOS = "read:SJL-folios"
    READ_SP_FOLIOS = "read:SP-folios"
    READ_UG_FOLIOS = "read:UG-folios"
    READ_USK_FOLIOS = "read:USK-folios"
    READ_WGL_FOLIOS = "read:WGL-folios"
    READ_WRM_FOLIOS = "read:WRM-folios"
    READ_BIBLIOGRAPHY = "read:bibliography"
    ANNOTATE_FRAGMENTS = "annotate:fragments"
    CREATE_TEXTS = "create:texts"
    LEMMATIZE_FRAGMENTS = "lemmatize:fragments"
    TRANSLITERATE_FRAGMENTS = "transliterate:fragments"
    WRITE_BIBLIOGRAPHY = "write:bibliography"
    WRITE_TEXTS = "write:texts"
    WRITE_WORDS = "write:words"
