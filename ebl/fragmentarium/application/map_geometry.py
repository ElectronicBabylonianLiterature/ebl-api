from __future__ import annotations

import hashlib
import math

Point = tuple[float, float]
Ring = tuple[Point, ...]
Rings = tuple[Ring, ...]
Polygon = tuple[Ring, ...]
MultiPolygon = tuple[Polygon, ...]

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


def canonical_geometry_checksum(geometry: MultiPolygon) -> str:
    return hashlib.sha1(_canonical_geometry(geometry).encode("utf-8")).hexdigest()[:12]


def _canonical_geometry(geometry: MultiPolygon) -> str:
    canonical_polygons = sorted(_canonical_polygon(polygon) for polygon in geometry)
    if not canonical_polygons:
        raise ValueError("Geometry must contain at least one polygon.")
    return "||".join(canonical_polygons)


def _canonical_polygon(polygon: Polygon) -> str:
    if not polygon:
        raise ValueError("Polygon must contain an exterior ring.")
    exterior, *holes = polygon
    canonical_exterior = _serialize_ring(_canonical_ring(exterior))
    canonical_holes = sorted(_serialize_ring(_canonical_ring(hole)) for hole in holes)
    return "|".join((canonical_exterior, *canonical_holes))


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


def reproject_geometry(
    geometry: MultiPolygon, source_crs: str, target_crs: str = CANONICAL_CRS
) -> MultiPolygon:
    from pyproj import Transformer

    transformer = Transformer.from_crs(source_crs, target_crs, always_xy=True)
    return tuple(
        tuple(tuple(transformer.transform(x, y) for x, y in ring) for ring in polygon)
        for polygon in geometry
    )


def geometry_bounds(geometry: MultiPolygon) -> tuple[float, float, float, float]:
    xs = [x for polygon in geometry for ring in polygon for x, _ in ring]
    ys = [y for polygon in geometry for ring in polygon for _, y in ring]
    return min(xs), min(ys), max(xs), max(ys)


def assert_plausible_geographic_bounds(geometry: MultiPolygon) -> None:
    if any(
        not math.isfinite(coordinate)
        for polygon in geometry
        for ring in polygon
        for point in ring
        for coordinate in point
    ):
        raise ValueError("Reprojected geometry contains non-finite coordinates.")
    min_x, min_y, max_x, max_y = geometry_bounds(geometry)
    if not (-180.0 <= min_x <= max_x <= 180.0 and -90.0 <= min_y <= max_y <= 90.0):
        raise ValueError(
            f"Reprojected geometry falls outside plausible EPSG:4326 bounds: "
            f"({min_x}, {min_y}, {max_x}, {max_y})"
        )


def polygonize_rings(rings: Rings) -> MultiPolygon:
    if not rings:
        raise ValueError("Geometry must contain at least one ring.")
    areas = tuple(_signed_area(ring) for ring in rings)
    for ring, area in strict_zip(rings, areas):
        _validate_ring(ring, area)
    for left_index, left in enumerate(rings):
        for right in rings[left_index + 1 :]:
            if _rings_intersect(left, right):
                raise ValueError("Polygon rings must not intersect or touch.")
    parents = tuple(_parent_index(index, rings, areas) for index in range(len(rings)))
    depths = tuple(_ring_depth(index, parents) for index in range(len(rings)))
    for area, depth in strict_zip(areas, depths):
        if (depth % 2 == 0 and area > 0) or (depth % 2 == 1 and area < 0):
            raise ValueError("Shapefile polygon ring orientation is invalid.")
    return tuple(
        (ring,)
        + tuple(
            rings[index]
            for index, parent in enumerate(parents)
            if parent == outer_index and depths[index] % 2 == 1
        )
        for outer_index, ring in enumerate(rings)
        if depths[outer_index] % 2 == 0
    )


def _signed_area(ring: Ring) -> float:
    return (
        sum(
            x * next_y - next_x * y
            for (x, y), (next_x, next_y) in strict_zip(ring[:-1], ring[1:])
        )
        / 2
    )


def _validate_ring(ring: Ring, area: float) -> None:
    _canonical_ring(ring)
    if area == 0:
        raise ValueError("Polygon rings must have non-zero area.")
    edges = tuple(strict_zip(ring[:-1], ring[1:]))
    last_index = len(edges) - 1
    for left_index, left in enumerate(edges):
        for right_index, right in enumerate(edges[left_index + 1 :], left_index + 1):
            if right_index == left_index + 1 or {left_index, right_index} == {
                0,
                last_index,
            }:
                continue
            if _segments_intersect(left, right):
                raise ValueError("Polygon rings must not self-intersect.")


def _rings_intersect(left: Ring, right: Ring) -> bool:
    return any(
        _segments_intersect(left_edge, right_edge)
        for left_edge in strict_zip(left[:-1], left[1:])
        for right_edge in strict_zip(right[:-1], right[1:])
    )


def _segments_intersect(left, right) -> bool:
    a, b = left
    c, d = right
    orientations = (
        _orientation(a, b, c),
        _orientation(a, b, d),
        _orientation(c, d, a),
        _orientation(c, d, b),
    )
    if orientations[0] * orientations[1] < 0 and orientations[2] * orientations[3] < 0:
        return True
    return any(
        orientation == 0 and _point_on_segment(point, segment)
        for orientation, point, segment in (
            (orientations[0], c, left),
            (orientations[1], d, left),
            (orientations[2], a, right),
            (orientations[3], b, right),
        )
    )


def _orientation(a: Point, b: Point, c: Point) -> float:
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def _point_on_segment(point: Point, segment) -> bool:
    start, end = segment
    return min(start[0], end[0]) <= point[0] <= max(start[0], end[0]) and min(
        start[1], end[1]
    ) <= point[1] <= max(start[1], end[1])


def _point_in_ring(point: Point, ring: Ring) -> bool:
    x, y = point
    inside = False
    for (left_x, left_y), (right_x, right_y) in strict_zip(ring[:-1], ring[1:]):
        if (left_y > y) != (right_y > y) and x < (
            (right_x - left_x) * (y - left_y) / (right_y - left_y) + left_x
        ):
            inside = not inside
    return inside


def _parent_index(index: int, rings: Rings, areas: tuple[float, ...]) -> int | None:
    containers = [
        candidate
        for candidate, ring in enumerate(rings)
        if candidate != index and _point_in_ring(rings[index][0], ring)
    ]
    return min(containers, key=lambda candidate: abs(areas[candidate]), default=None)


def _ring_depth(index: int, parents: tuple[int | None, ...]) -> int:
    depth = 0
    parent = parents[index]
    while parent is not None:
        depth += 1
        if depth > len(parents):
            raise ValueError("Polygon ring containment is cyclic.")
        parent = parents[parent]
    return depth
