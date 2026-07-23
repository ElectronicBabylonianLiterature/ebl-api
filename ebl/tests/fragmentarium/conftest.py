from typing import List

import pytest

from ebl.fragmentarium.domain.named_entity import (
    EntityAnnotationSpan,
    NamedEntityType,
    RealiaAnnotationSpan,
)
from ebl.realia.infrastructure.realia_schemas import RealiaEntrySchema
from ebl.tests.factories.realia import RealiaEntryFactory

KNOWN_REALIA_ID = "realia_000846"
OTHER_REALIA_ID = "realia_000847"
UNKNOWN_REALIA_ID = "realia_999999"


@pytest.fixture
def stored_realia(realia_repository) -> List[str]:
    realia_ids = [KNOWN_REALIA_ID, OTHER_REALIA_ID]
    for realia_id in realia_ids:
        entry = RealiaEntryFactory.build(
            realia_id=realia_id,
            related_terms=(),
            references=(),
            reallexikon=(),
        )
        realia_repository._realia_collection.insert_one(RealiaEntrySchema().dump(entry))
    return realia_ids


@pytest.fixture
def realia_annotation_spans() -> List[RealiaAnnotationSpan]:
    return [
        RealiaAnnotationSpan("Realia-1", KNOWN_REALIA_ID, ["Word-2", "Word-3"]),
        RealiaAnnotationSpan("Realia-2", OTHER_REALIA_ID, ["Word-7"]),
    ]


@pytest.fixture
def overlapping_annotation_spans() -> List[EntityAnnotationSpan]:
    return [
        EntityAnnotationSpan(
            "Entity-1", NamedEntityType.PERSONAL_NAME, ["Word-2", "Word-3"]
        )
    ]


@pytest.fixture
def overlapping_realia_spans() -> List[RealiaAnnotationSpan]:
    return [RealiaAnnotationSpan("Realia-1", KNOWN_REALIA_ID, ["Word-2", "Word-3"])]
