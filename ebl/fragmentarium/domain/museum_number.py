import attr
import re


def _is_not_empty(_, attribute: attr.Attribute, value: str) -> None:
    if not value:
        raise ValueError(f"Attribute {attribute} cannot be an empty string.")


def _does_not_contain_period(_, attribute: attr.Attribute, value: str) -> None:
    if "." in value:
        raise ValueError(f"Attribute {attribute} cannot contain '.'.")


def _require_suffix_if_contains_period(
    museum_number: "MuseumNumber", attribute: attr.Attribute, value: str
) -> None:
    if "." in value and not museum_number.suffix:
        raise ValueError("If {attribute} contains period suffix cannot be empty.")


@attr.s(auto_attribs=True, frozen=True)
class MuseumNumber:
    prefix: str = attr.ib(validator=[_is_not_empty, _require_suffix_if_contains_period])
    number: str = attr.ib(validator=[_is_not_empty, _does_not_contain_period])
    suffix: str = attr.ib(default="", validator=_does_not_contain_period)

    def __str__(self) -> str:
        if self.suffix:
            return f"{self.prefix}.{self.number}.{self.suffix}"
        else:
            return f"{self.prefix}.{self.number}"

    @staticmethod
    def of(source: str) -> "MuseumNumber":
        pattern = re.compile(r"(.+?)\.([^.]+)(?:\.([^.]+))?")
        match = pattern.fullmatch(source)
        if match:
            return MuseumNumber(match.group(1), match.group(2), match.group(3) or "")
        else:
            raise ValueError(f"'{source}' is not a valid museum number.")
