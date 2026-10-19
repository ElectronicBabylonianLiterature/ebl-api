from marshmallow import ValidationError

from ebl.realia.infrastructure.realia_schemas import RealiaEntrySchema


def is_loadable(document: dict) -> bool:
    try:
        RealiaEntrySchema().load(document)
    except ValidationError:
        return False
    return True
