from typing import List

from marshmallow import Schema, fields, post_load

from ebl.fragmentarium.domain.fragment import Fragment
from ebl.fragmentarium.domain.realia_info import RealiaInfo
from ebl.realia.application.realia_repository import RealiaRepository


class RealiaInfoSchema(Schema):
    realia_id = fields.String(required=True, data_key="realiaId")
    lemma = fields.String(required=True)
    type = fields.List(fields.String(), load_default=list)

    @post_load
    def make_realia_info(self, data, **kwargs) -> RealiaInfo:
        data["type"] = tuple(data["type"])
        return RealiaInfo(**data)


def resolve_realia_info(
    fragment: Fragment, realia_repository: RealiaRepository
) -> List[RealiaInfo]:
    realia_ids = sorted({entity.realia_id for entity in fragment.realia})
    entries = realia_repository.find_by_realia_ids(realia_ids)
    return [
        RealiaInfo(realia_id=entry.realia_id, lemma=entry.id, type=entry.type)
        for entry in sorted(entries, key=lambda entry: entry.realia_id)
    ]
