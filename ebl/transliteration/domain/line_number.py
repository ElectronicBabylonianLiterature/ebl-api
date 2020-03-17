from typing import Optional

import attr


@attr.s(auto_attribs=True, frozen=True)
class LineNumber:
    number: int
    has_prime: bool = False
    prefix_modifier: Optional[str] = None
    suffix_modifier: Optional[str] = None

    @property
    def atf(self) -> str:
        prefix = f"{self.prefix_modifier}+" if self.prefix_modifier else ""
        prime = "'" if self.has_prime else ""
        suffix = self.suffix_modifier or ""
        return f"{prefix}{self.number}{prime}{suffix}."
