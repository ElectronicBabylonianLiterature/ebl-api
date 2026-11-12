from marshmallow import fields

from ebl.schemas import ValueEnumField
from ebl.transliteration.application.storage_serialization import omitted_when_default
from ebl.transliteration.domain.atf import Flag


def flag_list_field() -> fields.List:
    return fields.List(
        ValueEnumField(Flag), load_default=list, metadata=omitted_when_default()
    )


def modifier_list_field() -> fields.List:
    return fields.List(
        fields.String(), load_default=list, metadata=omitted_when_default()
    )
