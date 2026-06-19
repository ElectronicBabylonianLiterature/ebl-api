import pytest

from ebl.bibliography.application.external_mapping import (
    external_mapping_key,
    normalize_external_mapping,
)


def test_normalize_external_mapping() -> None:
    assert normalize_external_mapping(
        {
            "partner": " partner-x ",
            "externalId": " ref-123 ",
            "externalUrl": "https://partner.example/refs/ref-123",
            "bibliographyId": " Q30000000 ",
        }
    ) == {
        "partner": "partner-x",
        "externalId": "ref-123",
        "externalUrl": "https://partner.example/refs/ref-123",
        "bibliographyId": "Q30000000",
    }


def test_external_mapping_key_uses_partner_and_external_id() -> None:
    assert external_mapping_key({"partner": "partner-x", "externalId": "ref-123"}) == (
        "partner-x",
        "ref-123",
    )


def test_normalize_external_mapping_requires_partner_and_external_id() -> None:
    with pytest.raises(ValueError, match="partner is required"):
        normalize_external_mapping({"externalId": "ref-123"})
    with pytest.raises(ValueError, match="externalId is required"):
        normalize_external_mapping({"partner": "partner-x"})


def test_normalize_external_mapping_rejects_non_http_url() -> None:
    with pytest.raises(ValueError, match="HTTP or HTTPS"):
        normalize_external_mapping(
            {
                "partner": "partner-x",
                "externalId": "ref-123",
                "externalUrl": "file:///tmp/ref-123",
            }
        )
