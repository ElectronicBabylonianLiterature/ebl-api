from typing import Mapping, Optional, Sequence, Tuple

import attr

NO_LANGUAGE = "none"


@attr.attrs(auto_attribs=True, frozen=True)
class LanguageMap:
    entries: Mapping[str, Tuple[str, ...]]

    @staticmethod
    def of(value: str, language: str = NO_LANGUAGE) -> "LanguageMap":
        return LanguageMap({language: (value,)})

    @staticmethod
    def optional(
        value: Optional[str], language: str = NO_LANGUAGE
    ) -> Optional["LanguageMap"]:
        return None if value is None else LanguageMap.of(value, language)

    @staticmethod
    def of_all(values: Sequence[str], language: str = NO_LANGUAGE) -> "LanguageMap":
        return LanguageMap({language: tuple(values)})

    def to_dict(self) -> Mapping[str, Sequence[str]]:
        return {language: list(values) for language, values in self.entries.items()}
