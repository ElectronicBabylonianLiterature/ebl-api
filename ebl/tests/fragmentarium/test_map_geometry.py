import pytest

from ebl.fragmentarium.application.map_geometry import (
    assert_plausible_geographic_bounds,
    canonical_geometry_checksum,
    geometry_bounds,
    polygonize_rings,
    reproject_geometry,
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

    checksum = canonical_geometry_checksum(((ring,),))

    assert checksum == "40bccb23137e"
    assert canonical_geometry_checksum(((rotated,),)) == checksum
    assert canonical_geometry_checksum(((reversed_ring,),)) == checksum


def test_checksum_rejects_unclosed_ring():
    with pytest.raises(ValueError, match="closed"):
        canonical_geometry_checksum(((((43.0, 35.0), (43.1, 35.0), (43.1, 35.1)),),))


def test_reproject_web_mercator_to_wgs84_near_kalhu():
    web_mercator_kalhu = (4825000.0, 4315000.0)
    ring = (
        web_mercator_kalhu,
        (4825100.0, 4315000.0),
        (4825100.0, 4315100.0),
        web_mercator_kalhu,
    )

    reprojected = reproject_geometry(((ring,),), "EPSG:3857")
    min_x, min_y, max_x, max_y = geometry_bounds(reprojected)

    assert 42.0 < min_x < 44.0
    assert 35.0 < min_y < 37.0
    assert_plausible_geographic_bounds(reprojected)


def test_assert_plausible_geographic_bounds_rejects_out_of_range():
    with pytest.raises(ValueError, match="plausible"):
        assert_plausible_geographic_bounds(
            (
                (
                    (
                        (200.0, 35.0),
                        (200.1, 35.0),
                        (200.1, 35.1),
                        (200.0, 35.0),
                    ),
                ),
            )
        )


def test_assert_plausible_geographic_bounds_rejects_non_finite_values():
    with pytest.raises(ValueError, match="non-finite"):
        assert_plausible_geographic_bounds(
            (
                (
                    (
                        (43.0, 35.0),
                        (float("nan"), 35.0),
                        (43.1, 35.1),
                        (43.0, 35.0),
                    ),
                ),
            )
        )


def test_polygonize_rings_preserves_holes_and_multiple_exteriors():
    exterior = ((0.0, 0.0), (0.0, 10.0), (10.0, 10.0), (10.0, 0.0), (0.0, 0.0))
    hole = ((2.0, 2.0), (8.0, 2.0), (8.0, 8.0), (2.0, 8.0), (2.0, 2.0))
    second_exterior = (
        (20.0, 0.0),
        (20.0, 5.0),
        (25.0, 5.0),
        (25.0, 0.0),
        (20.0, 0.0),
    )

    assert polygonize_rings((hole, second_exterior, exterior)) == (
        (second_exterior,),
        (exterior, hole),
    )


def test_checksum_preserves_polygon_and_hole_grouping():
    first = ((0.0, 0.0), (0.0, 10.0), (10.0, 10.0), (10.0, 0.0), (0.0, 0.0))
    second = ((2.0, 2.0), (8.0, 2.0), (8.0, 8.0), (2.0, 8.0), (2.0, 2.0))

    assert canonical_geometry_checksum(((first, second),)) != (
        canonical_geometry_checksum(((first,), (second,)))
    )


@pytest.mark.parametrize(
    "rings, message",
    [
        (
            (
                ((0.0, 0.0), (0.0, 4.0), (4.0, 4.0), (4.0, 0.0), (0.0, 0.0)),
                ((2.0, -1.0), (2.0, 3.0), (3.0, 3.0), (3.0, -1.0), (2.0, -1.0)),
            ),
            "intersect",
        ),
        (
            (
                ((0.0, 0.0), (0.0, 4.0), (4.0, 4.0), (4.0, 0.0), (0.0, 0.0)),
                ((1.0, 1.0), (1.0, 3.0), (3.0, 3.0), (3.0, 1.0), (1.0, 1.0)),
            ),
            "orientation",
        ),
    ],
)
def test_polygonize_rings_rejects_invalid_topology(rings, message):
    with pytest.raises(ValueError, match=message):
        polygonize_rings(rings)
