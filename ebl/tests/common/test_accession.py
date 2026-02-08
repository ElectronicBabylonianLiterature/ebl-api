import pytest
from ebl.common.application.schemas import AccessionSchema
from ebl.common.domain.accession import Accession


ACCESSION = Accession("A", "38")
ACCESSION_DTO = {"prefix": "A", "number": "38", "suffix": ""}


def test_of():
    assert Accession.of("A.38") == ACCESSION


def test_of_invalid():
    with pytest.raises(ValueError, match="'invalid.' is not a valid accession number."):
        Accession.of("invalid.")


def test_serialize():
    assert AccessionSchema().dump(ACCESSION) == ACCESSION_DTO


def test_deserialize():
    assert AccessionSchema().load(ACCESSION_DTO) == ACCESSION
