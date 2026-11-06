import pytest

from ebl.fragmentarium.application.map_artifact_repository import MapArtifactRepository
from ebl.fragmentarium.application.map_site_config import SITE_CONFIGS


@pytest.mark.parametrize("site_id", tuple(SITE_CONFIGS))
def test_repository_declares_canonical_site_metadata(site_id: str) -> None:
    assert MapArtifactRepository.supports_site(site_id)
    assert MapArtifactRepository.site_name(site_id) == SITE_CONFIGS[site_id].site_name


def test_repository_rejects_unknown_site_metadata() -> None:
    assert not MapArtifactRepository.supports_site("UNKNOWN")
    with pytest.raises(ValueError, match="Unknown map site"):
        MapArtifactRepository.site_name("UNKNOWN")
