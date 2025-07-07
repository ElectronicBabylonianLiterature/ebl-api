from enum import Enum
import re

OPEN = True
RESTRICTED = False


class ScopeItem(Enum):
    def __init__(self, scope_string: str, is_open=True):
        prefix, name, suffix = self._parse_scope_string(scope_string)
        self.prefix = prefix
        self.scope_name = name
        self.suffix = suffix
        self.is_open = is_open

    @classmethod
    def from_string(cls, scope_string: str):
        prefix, name, suffix = cls._parse_scope_string(scope_string)
        try:
            return next(
                enum
                for enum in cls
                if enum.prefix == prefix
                and enum.scope_name == name
                and suffix in [enum.suffix, ""]
            )
        except StopIteration:
            raise ValueError(f"Unknown scope: {scope_string}")

    @staticmethod
    def _parse_scope_string(scope_string: str):
        if match := re.match("([^:]+):([^-]+)(?:-(.+))?", scope_string):
            return match[1], match[2], match[3] or ""
        else:
            raise ValueError(f"Unexepcted scope format: {scope_string!r}")

    @property
    def is_restricted(self) -> bool:
        return not self.is_open

    def __str__(self):
        suffix = f"-{self.suffix}" if self.suffix else ""
        return f"{self.prefix}:{self.scope_name}{suffix}"


class Scope(ScopeItem):
    READ_CAIC_FRAGMENTS = ("read:CAIC-fragments", RESTRICTED)
    READ_ITALIANNINEVEH_FRAGMENTS = ("read:ITALIANNINEVEH-fragments", RESTRICTED)
    READ_SIPPARLIBRARY_FRAGMENTS = ("read:SIPPARLIBRARY-fragments", RESTRICTED)
    READ_SIPPARISTANBUL_FRAGMENTS = ("read:SIPPARISTANBUL-fragments", RESTRICTED)
    READ_COPENHAGEN_FRAGMENTS = ("read:COPENHAGEN-fragments", RESTRICTED)
    READ_URUKLBU_FRAGMENTS = ("read:URUKLBU-fragments", RESTRICTED)
    READ_ARG_FOLIOS = ("read:ARG-folios", RESTRICTED)
    READ_EVW_FOLIOS = ("read:EVW-folios", RESTRICTED)
    READ_ILF_FOLIOS = ("read:ILF-folios", RESTRICTED)
    READ_HHF_FOLIOS = ("read:HHF-folios", OPEN)
    READ_JNP_FOLIOS = ("read:JNP-folios", RESTRICTED)
    READ_MJG_FOLIOS = ("read:MJG-folios", RESTRICTED)
    READ_SJL_FOLIOS = ("read:SJL-folios", OPEN)
    READ_SP_FOLIOS = ("read:SP-folios", RESTRICTED)
    READ_UG_FOLIOS = ("read:UG-folios", RESTRICTED)
    READ_USK_FOLIOS = ("read:USK-folios", RESTRICTED)
    READ_WRM_FOLIOS = ("read:WRM-folios", RESTRICTED)
    READ_AKG_FOLIOS = ("read:AKG-folios", OPEN)
    READ_CB_FOLIOS = ("read:CB-folios", OPEN)
    READ_EL_FOLIOS = ("read:EL-folios", OPEN)
    READ_ER_FOLIOS = ("read:ER-folios", OPEN)
    READ_FWG_FOLIOS = ("read:FWG-folios", OPEN)
    READ_GS_FOLIOS = ("read:GS-folios", OPEN)
    READ_JA_FOLIOS = ("read:JA-folios", OPEN)
    READ_JLP_FOLIOS = ("read:JLP-folios", RESTRICTED)
    READ_JS_FOLIOS = ("read:JS-folios", OPEN)
    READ_LV_FOLIOS = ("read:LV-folios", OPEN)
    READ_RB_FOLIOS = ("read:RB-folios", OPEN)
    READ_WGL_FOLIOS = ("read:WGL-folios", OPEN)
    READ_BIBLIOGRAPHY = ("read:bibliography", OPEN)
    ANNOTATE_FRAGMENTS = ("annotate:fragments", RESTRICTED)
    CREATE_TEXTS = ("create:texts", RESTRICTED)
    LEMMATIZE_FRAGMENTS = ("lemmatize:fragments", RESTRICTED)
    TRANSLITERATE_FRAGMENTS = ("transliterate:fragments", RESTRICTED)
    WRITE_BIBLIOGRAPHY = ("write:bibliography", RESTRICTED)
    WRITE_TEXTS = ("write:texts", RESTRICTED)
    READ_WORDS = ("read:words", OPEN)
    READ_TEXTS = ("read:texts", OPEN)
    WRITE_WORDS = ("write:words", RESTRICTED)
