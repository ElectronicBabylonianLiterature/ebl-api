from typing import Optional, Sequence, TypeVar

import attr

T = TypeVar("T")


def not_blank(_instance: object, attribute: attr.Attribute, value: object) -> None:
    if not isinstance(value, str):
        raise ValueError(f"Attribute {attribute.name} must be a string.")
    if not value.strip():
        raise ValueError(f"Attribute {attribute.name} cannot be blank.")


def strict_int(attribute: attr.Attribute, value: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"Attribute {attribute.name} must be an integer.")


def positive_int(_instance: object, attribute: attr.Attribute, value: int) -> None:
    strict_int(attribute, value)
    if value <= 0:
        raise ValueError(f"Attribute {attribute.name} must be positive.")


def non_negative_int(_instance: object, attribute: attr.Attribute, value: int) -> None:
    strict_int(attribute, value)
    if value < 0:
        raise ValueError(f"Attribute {attribute.name} cannot be negative.")


def strict_bool(_instance: object, attribute: attr.Attribute, value: bool) -> None:
    if not isinstance(value, bool):
        raise ValueError(f"Attribute {attribute.name} must be a boolean.")


def tuple_or_empty(value: Optional[Sequence[T]]) -> tuple[T, ...]:
    return tuple(value or ())
