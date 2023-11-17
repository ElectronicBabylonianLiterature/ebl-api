from ebl.common.application.schemas import AccessionSchema
from ebl.common.domain.accession import Accession
from ebl.transliteration.application.museum_number_schema import MuseumNumberSchema
from ebl.transliteration.domain.museum_number import MuseumNumber


def museum_number_is(number: MuseumNumber) -> dict:
    serialized = MuseumNumberSchema().dump(number)
    return {f"museumNumber.{key}": value for key, value in serialized.items()}


def accession_is(accession: Accession) -> dict:
    serialized = AccessionSchema().dump(accession)
    return {f"accession.{key}": value for key, value in serialized.items()}
