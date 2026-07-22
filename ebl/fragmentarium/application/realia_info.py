from typing import Dict, List, Sequence

from marshmallow import Schema, fields, post_load
from pymongo.errors import PyMongoError

from ebl.fragmentarium.domain.fragment import Fragment
from ebl.fragmentarium.domain.realia_info import RealiaInfo
from ebl.realia.application.realia_repository import RealiaRepository
from ebl.realia.domain.realia_entry import RealiaEntry


class RealiaInfoSchema(Schema):
    realia_id = fields.String(required=True, data_key="realiaId")
    lemma = fields.String(required=True)
    type = fields.List(fields.String(), load_default=list)

    @post_load
    def make_realia_info(self, data, **kwargs) -> RealiaInfo:
        data["type"] = tuple(data["type"])
        return RealiaInfo(**data)


def _to_realia_info(entry: RealiaEntry) -> RealiaInfo:
    return RealiaInfo(realia_id=entry.realia_id, lemma=entry.id, type=entry.type)


def _find_by_realia_ids(
    realia_repository: RealiaRepository, realia_ids: Sequence[str]
) -> Sequence[RealiaEntry]:
    try:
        return realia_repository.find_by_realia_ids(realia_ids)
    except PyMongoError:
        return []


def resolve_realia_info(
    fragment: Fragment, realia_repository: RealiaRepository
) -> List[RealiaInfo]:
    realia_ids = sorted({entity.realia_id for entity in fragment.realia})
    if not realia_ids:
        return []
    entries = _find_by_realia_ids(realia_repository, realia_ids)
    return [
        _to_realia_info(entry)
        for entry in sorted(entries, key=lambda entry: entry.realia_id)
    ]


def _document_realia_ids(document: dict) -> List[str]:
    return sorted({realia["realiaId"] for realia in document.get("realia", [])})


def resolve_realia_info_map(
    documents: Sequence[dict], realia_repository: RealiaRepository
) -> Dict[str, RealiaInfo]:
    all_realia_ids = sorted(
        {
            realia_id
            for document in documents
            for realia_id in _document_realia_ids(document)
        }
    )
    if not all_realia_ids:
        return {}
    return {
        entry.realia_id: _to_realia_info(entry)
        for entry in _find_by_realia_ids(realia_repository, all_realia_ids)
    }


def document_realia_info(
    document: dict, info_by_realia_id: Dict[str, RealiaInfo]
) -> List[RealiaInfo]:
    return [
        info_by_realia_id[realia_id]
        for realia_id in _document_realia_ids(document)
        if realia_id in info_by_realia_id
    ]
