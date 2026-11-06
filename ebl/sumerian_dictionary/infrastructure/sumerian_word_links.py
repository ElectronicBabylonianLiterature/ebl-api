from typing import Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

import attr

from ebl.mongo_collection import MongoCollection
from ebl.sumerian_dictionary.domain.sumerian_word import SumerianWord
from ebl.sumerian_dictionary.domain.sumerian_word_links import (
    CrossReference,
    WordLink,
)

LINK_PROJECTION = {"citationForm": 1, "homonym": 1, "guideWord": 1}

LinkTargets = Mapping[str, Mapping[str, object]]


def _links(word: SumerianWord) -> Iterable[WordLink]:
    if word.head is not None:
        yield word.head
    yield from word.compounds
    yield from word.name_compounds
    for cross_reference in word.cross_references:
        yield from cross_reference.targets
        yield from cross_reference.name_targets


def linked_ids(word: SumerianWord) -> List[str]:
    return list(dict.fromkeys(link.id for link in _links(word)))


def fetch_link_targets(
    collection: MongoCollection, ids: Sequence[str]
) -> Dict[str, Mapping[str, object]]:
    if not ids:
        return {}
    documents = collection.find_many(
        {"_id": {"$in": list(ids)}}, projection=LINK_PROJECTION
    )
    return {document["_id"]: document for document in documents}


def _text(target: Mapping[str, object], key: str) -> str:
    value = target.get(key)
    return value if isinstance(value, str) else ""


def _resolve(link: WordLink, targets: LinkTargets) -> WordLink:
    target = targets.get(link.id)
    if target is None:
        return link
    return attr.evolve(
        link,
        citation_form=link.citation_form or _text(target, "citationForm"),
        homonym=_text(target, "homonym"),
        guide_word=_text(target, "guideWord"),
    )


def _resolve_all(
    links: Sequence[WordLink], targets: LinkTargets
) -> Tuple[WordLink, ...]:
    return tuple(_resolve(link, targets) for link in links)


def _resolve_head(head: Optional[WordLink], targets: LinkTargets) -> Optional[WordLink]:
    return None if head is None else _resolve(head, targets)


def _resolve_cross_reference(
    cross_reference: CrossReference, targets: LinkTargets
) -> CrossReference:
    return attr.evolve(
        cross_reference,
        targets=_resolve_all(cross_reference.targets, targets),
        name_targets=_resolve_all(cross_reference.name_targets, targets),
    )


def resolve_links(word: SumerianWord, targets: LinkTargets) -> SumerianWord:
    return attr.evolve(
        word,
        head=_resolve_head(word.head, targets),
        compounds=_resolve_all(word.compounds, targets),
        name_compounds=_resolve_all(word.name_compounds, targets),
        cross_references=tuple(
            _resolve_cross_reference(cross_reference, targets)
            for cross_reference in word.cross_references
        ),
    )
