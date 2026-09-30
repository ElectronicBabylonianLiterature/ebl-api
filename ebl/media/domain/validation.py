from collections.abc import Callable, Sequence
from typing import Optional, TypeVar, cast

import attr

T = TypeVar("T")
AttrsValidator = Callable[[object, attr.Attribute, object], None]


def not_blank(_instance: object, attribute: attr.Attribute, value: object) -> None:
    if not isinstance(value, str):
        raise ValueError(f"Attribute {attribute.name} must be a string.")
    if not value.strip():
        raise ValueError(f"Attribute {attribute.name} cannot be blank.")


def strict_int(attribute: attr.Attribute, value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"Attribute {attribute.name} must be an integer.")
    return value


def positive_int(_instance: object, attribute: attr.Attribute, value: object) -> None:
    if strict_int(attribute, value) <= 0:
        raise ValueError(f"Attribute {attribute.name} must be positive.")


def non_negative_int(
    _instance: object, attribute: attr.Attribute, value: object
) -> None:
    if strict_int(attribute, value) < 0:
        raise ValueError(f"Attribute {attribute.name} cannot be negative.")


def strict_bool(_instance: object, attribute: attr.Attribute, value: object) -> None:
    if not isinstance(value, bool):
        raise ValueError(f"Attribute {attribute.name} must be a boolean.")


def instance_of(expected_type: type[object]) -> AttrsValidator:
    def validate(_instance: object, attribute: attr.Attribute, value: object) -> None:
        if not isinstance(value, expected_type):
            raise ValueError(
                f"Attribute {attribute.name} must be a {expected_type.__name__}."
            )

    return validate


def optional_instance_of(expected_type: type[object]) -> AttrsValidator:
    required_validator = instance_of(expected_type)

    def validate(instance: object, attribute: attr.Attribute, value: object) -> None:
        if value is not None:
            required_validator(instance, attribute, value)

    return validate


def items_instance_of(expected_type: type[object]) -> AttrsValidator:
    def validate(_instance: object, attribute: attr.Attribute, value: object) -> None:
        items = cast(Sequence[object], value)
        if any(not isinstance(item, expected_type) for item in items):
            raise ValueError(
                f"Attribute {attribute.name} must contain only "
                f"{expected_type.__name__} values."
            )

    return validate


def tuple_or_empty(value: Optional[Sequence[T]]) -> tuple[T, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("Value must be a sequence, not a string.")
    if value is None:
        return ()
    return tuple(value)
