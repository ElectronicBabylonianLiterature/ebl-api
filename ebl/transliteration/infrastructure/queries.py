from typing import Union

from ebl.transliteration.application.museum_number_schema import MuseumNumberSchema
from ebl.transliteration.domain.museum_number import MuseumNumber


def museum_number_is(number: Union[MuseumNumber, dict]) -> dict:
    serialized = (
        MuseumNumberSchema().dump(number)
        if isinstance(number, MuseumNumber)
        else number
    )
    return {f"museumNumber.{key}": value for key, value in serialized.items()}
