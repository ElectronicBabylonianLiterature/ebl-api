from __future__ import annotations

import hashlib

Point = tuple[float, float]
Ring = tuple[Point, ...]
Rings = tuple[Ring, ...]

CANONICAL_CRS = "EPSG:4326"


def strict_zip(*iterables):
    materialized = [tuple(iterable) for iterable in iterables]
    lengths = {len(items) for items in materialized}
    if len(lengths) > 1:
        raise ValueError(
            f"strict_zip length mismatch: {[len(items) for items in materialized]}"
        )
    length = lengths.pop() if lengths else 0
    return [tuple(items[index] for items in materialized) for index in range(length)]


def canonical_geometry_checksum(rings: Rings) -> str:
    return hashlib.sha1(_canonical_geometry(rings).encode("utf-8")).hexdigest()[:12]


def _canonical_geometry(rings: Rings) -> str:
    canonical_rings = sorted(_serialize_ring(_canonical_ring(ring)) for ring in rings)
    if not canonical_rings:
        raise ValueError("Polygon must contain at least one ring.")
    return "|".join(canonical_rings)


def _canonical_ring(ring: Ring) -> Ring:
    if len(ring) < 4 or ring[0] != ring[-1]:
        raise ValueError("Polygon rings must be explicitly closed.")
    vertices = ring[:-1]
    if len(set(vertices)) < 3:
        raise ValueError("Polygon rings must contain at least three distinct points.")
    clockwise = _best_rotation(vertices)
    counter_clockwise = _best_rotation(tuple(reversed(vertices)))
    best = min(clockwise, counter_clockwise, key=_serialize_ring)
    return best + (best[0],)


def _best_rotation(vertices: Ring) -> Ring:
    return min(
        (vertices[index:] + vertices[:index] for index in range(len(vertices))),
        key=_serialize_ring,
    )


def _serialize_ring(ring: Ring) -> str:
    return ";".join(f"{_format_coordinate(x)},{_format_coordinate(y)}" for x, y in ring)


def _format_coordinate(value: float) -> str:
    return format(value, ".15f").rstrip("0").rstrip(".")


def reproject_rings(
    rings: Rings, source_crs: str, target_crs: str = CANONICAL_CRS
) -> Rings:
    from pyproj import Transformer

    transformer = Transformer.from_crs(source_crs, target_crs, always_xy=True)
    return tuple(tuple(transformer.transform(x, y) for x, y in ring) for ring in rings)


def rings_bounds(rings: Rings) -> tuple[float, float, float, float]:
    xs = [x for ring in rings for x, _ in ring]
    ys = [y for ring in rings for _, y in ring]
    return min(xs), min(ys), max(xs), max(ys)


def assert_plausible_geographic_bounds(rings: Rings) -> None:
    min_x, min_y, max_x, max_y = rings_bounds(rings)
    if not (-180.0 <= min_x <= max_x <= 180.0 and -90.0 <= min_y <= max_y <= 90.0):
        raise ValueError(
            f"Reprojected geometry falls outside plausible EPSG:4326 bounds: "
            f"({min_x}, {min_y}, {max_x}, {max_y})"
        )
