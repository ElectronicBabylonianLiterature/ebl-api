from typing import Callable, ClassVar, Mapping

from marshmallow import EXCLUDE, Schema, post_load

LANGUAGES = ("SUMERIAN", "EMESAL")
DICTIONARY_SOURCES = ("attinger", "epsd2")
ATTINGER_SOURCE = ("attinger",)
BORGER_SOURCE = ("borger",)
RENDERING_KINDS = ("key", "variant", "form")
SIGN_LISTS = ("ebl", "ogsl")
OPTIONAL_SIGN_LISTS = ("", *SIGN_LISTS)
UNRENDERED_REASONS = ("unread", "unresolved", "gap", "noCharacter")
CROSS_REFERENCE_RELATIONS = ("see", "compare")
ALIAS_RELATIONS = ("see", "equals")


def _freeze(value: object) -> object:
    return tuple(value) if isinstance(value, list) else value


def undeclared_model(**data: object) -> object:
    raise NotImplementedError("The schema declares no model.")


class AttrsSchema(Schema):
    model: ClassVar[Callable[..., object]] = undeclared_model

    class Meta:
        unknown = EXCLUDE

    @post_load
    def make_object(self, data: Mapping[str, object], **kwargs) -> object:
        return type(self).model(**{key: _freeze(value) for key, value in data.items()})
