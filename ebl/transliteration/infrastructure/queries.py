from functools import singledispatch
from ebl.common.application.schemas import AccessionSchema
from ebl.common.domain.accession import Accession
from ebl.fragmentarium.application.archaeology_schemas import ExcavationNumberSchema
from ebl.fragmentarium.domain.archaeology import ExcavationNumber
from ebl.transliteration.application.museum_number_schema import MuseumNumberSchema
from ebl.transliteration.domain.museum_number import MuseumNumber


@singledispatch
def query_number_is(number, allow_wildcard=False) -> dict:
    raise ValueError(f"Unknown number type: {type(number)}")


def replace_suffix(serialized: dict) -> dict:
    suffix = serialized["suffix"]
    return {
        **serialized,
        "suffix": "*" if serialized["number"] == "*" and not suffix else suffix,
    }


def build_query(path_prefix: str, serialized: dict, allow_wildcard: bool) -> dict:
    serialized = replace_suffix(serialized) if allow_wildcard else serialized

    return {
        f"{path_prefix}.{key}": value
        for key, value in serialized.items()
        if not (allow_wildcard and value == "*")
    }


@query_number_is.register
def _(number: MuseumNumber, allow_wildcard=False) -> dict:
    serialized = MuseumNumberSchema().dump(number)
    return build_query("museumNumber", serialized, allow_wildcard)


@query_number_is.register
def _(accession: Accession, allow_wildcard=False) -> dict:
    serialized = AccessionSchema().dump(accession)
    return build_query("accession", serialized, allow_wildcard)


@query_number_is.register
def _(number: ExcavationNumber, allow_wildcard=False) -> dict:
    serialized = ExcavationNumberSchema().dump(number)
    return build_query("archaeology.excavationNumber", serialized, allow_wildcard)
