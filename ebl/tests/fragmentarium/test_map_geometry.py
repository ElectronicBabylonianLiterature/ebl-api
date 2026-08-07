import pytest

from ebl.fragmentarium.application.map_geometry import (
    assert_plausible_geographic_bounds,
    canonical_geometry_checksum,
    reproject_rings,
    rings_bounds,
    strict_zip,
)


def test_strict_zip_matches_equal_length():
    assert list(strict_zip([1, 2], [3, 4])) == [(1, 3), (2, 4)]


def test_strict_zip_rejects_length_mismatch():
    with pytest.raises(ValueError, match="length mismatch"):
        list(strict_zip([1, 2], [3]))


def test_checksum_stable_across_rotation_and_orientation():
    ring = (
        (43.0, 35.0),
        (43.1, 35.0),
        (43.1, 35.1),
        (43.0, 35.1),
        (43.0, 35.0),
    )
    rotated = ring[1:-1] + ring[:2]
    reversed_ring = tuple(reversed(ring))

    checksum = canonical_geometry_checksum((ring,))

    assert canonical_geometry_checksum((rotated,)) == checksum
    assert canonical_geometry_checksum((reversed_ring,)) == checksum


def test_checksum_rejects_unclosed_ring():
    with pytest.raises(ValueError, match="closed"):
        canonical_geometry_checksum((((43.0, 35.0), (43.1, 35.0), (43.1, 35.1)),))


def test_reproject_web_mercator_to_wgs84_near_kalhu():
    web_mercator_kalhu = (4825000.0, 4315000.0)
    ring = (
        web_mercator_kalhu,
        (4825100.0, 4315000.0),
        (4825100.0, 4315100.0),
        web_mercator_kalhu,
    )

    reprojected = reproject_rings((ring,), "EPSG:3857")
    min_x, min_y, max_x, max_y = rings_bounds(reprojected)

    assert 42.0 < min_x < 44.0
    assert 35.0 < min_y < 37.0
    assert_plausible_geographic_bounds(reprojected)


def test_assert_plausible_geographic_bounds_rejects_out_of_range():
    with pytest.raises(ValueError, match="plausible"):
        assert_plausible_geographic_bounds(
            (((200.0, 35.0), (200.1, 35.0), (200.1, 35.1), (200.0, 35.0)),)
        )
