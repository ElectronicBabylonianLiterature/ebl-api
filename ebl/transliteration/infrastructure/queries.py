from functools import singledispatch
from ebl.common.application.schemas import AccessionSchema
from ebl.common.domain.accession import Accession
from ebl.fragmentarium.application.archaeology_schemas import ExcavationNumberSchema
from ebl.fragmentarium.domain.archaeology import ExcavationNumber
from ebl.transliteration.application.museum_number_schema import MuseumNumberSchema
from ebl.transliteration.domain.museum_number import MuseumNumber


@singledispatch
def query_number_is(number) -> dict:
    raise ValueError(f"Unknown number type: {type(number)}")


@query_number_is.register
def _(number: MuseumNumber) -> dict:
    serialized = MuseumNumberSchema().dump(number)
    return {f"museumNumber.{key}": value for key, value in serialized.items()}


@query_number_is.register
def _(accession: Accession) -> dict:
    serialized = AccessionSchema().dump(accession)
    return {f"accession.{key}": value for key, value in serialized.items()}


@query_number_is.register
def _(number: ExcavationNumber) -> dict:
    serialized = ExcavationNumberSchema().dump(number)
    return {
        f"archaeology.excavationNumber.{key}": value
        for key, value in serialized.items()
    }
