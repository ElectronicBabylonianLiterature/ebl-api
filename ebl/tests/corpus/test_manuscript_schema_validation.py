from typing import Any, cast

import pytest
from marshmallow import ValidationError

from ebl.common.domain.manuscript_type import ManuscriptType
from ebl.common.domain.period import Period
from ebl.corpus.application.schemas import ManuscriptSchema
from ebl.corpus.domain.manuscript import Manuscript
from ebl.provenance.application.provenance_service import ProvenanceService


@pytest.mark.parametrize(
    "provenance,period,manuscript_type,message",
    [
        (
            "Standard Text",
            Period.NEO_ASSYRIAN,
            ManuscriptType.NONE,
            "period and type must be None if provenance is Standard Text",
        ),
        (
            "Nineveh",
            Period.NONE,
            ManuscriptType.LIBRARY,
            "period and type must not be None if provenance is not Standard Text",
        ),
    ],
)
def test_manuscript_schema_rejects_invalid_provenance_combinations(
    seeded_provenance_service: ProvenanceService,
    provenance: str,
    period: Period,
    manuscript_type: ManuscriptType,
    message: str,
) -> None:
    schema = ManuscriptSchema(context={"provenance_service": seeded_provenance_service})
    payload = cast(dict[str, Any], schema.dump(Manuscript(1)))
    payload.update(
        provenance=provenance,
        period=period.long_name,
        type=manuscript_type.long_name,
    )

    with pytest.raises(ValidationError) as error:
        schema.load(payload)

    assert error.value.messages == {"_schema": [message]}
