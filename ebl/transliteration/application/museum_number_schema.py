from marshmallow import post_load
from ebl.transliteration.domain.museum_number import MuseumNumber
from ebl.common.application.schemas import AbstractMuseumNumberSchema


class MuseumNumberSchema(AbstractMuseumNumberSchema):
    @post_load
    def create_museum_number(self, data, **kwargs) -> MuseumNumber:
        return MuseumNumber(**data)
