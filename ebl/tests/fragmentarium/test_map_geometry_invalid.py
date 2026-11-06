from ebl.fragmentarium.application.map_geometry import Rings, MultiPolygon
import pytest

from ebl.fragmentarium.application import map_geometry


@pytest.mark.parametrize(
    "geometry, message",
    [
        ((), "at least one polygon"),
        (((),), "exterior ring"),
        (
            ((((0.0, 0.0), (1.0, 0.0), (0.0, 0.0), (0.0, 0.0)),),),
            "three distinct points",
        ),
    ],
)
def test_checksum_rejects_degenerate_geometry(
    geometry: MultiPolygon, message: str
) -> None:
    with pytest.raises(ValueError, match=message):
        map_geometry.canonical_geometry_checksum(geometry)


@pytest.mark.parametrize(
    "rings, message",
    [
        ((), "at least one ring"),
        (
            (((0.0, 0.0), (1.0, 1.0), (2.0, 2.0), (0.0, 0.0)),),
            "non-zero area",
        ),
        (
            (((0.0, 0.0), (3.0, 3.0), (0.0, 3.0), (2.0, 0.0), (0.0, 0.0)),),
            "self-intersect",
        ),
    ],
)
def test_polygonization_rejects_empty_or_invalid_rings(
    rings: Rings, message: str
) -> None:
    with pytest.raises(ValueError, match=message):
        map_geometry.polygonize_rings(rings)


def test_ring_depth_rejects_cyclic_containment() -> None:
    with pytest.raises(ValueError, match="cyclic"):
        map_geometry._ring_depth(0, (1, 0))
