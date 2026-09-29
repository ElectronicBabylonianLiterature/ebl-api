import struct


def dbf_bytes(value: bytes = b"Room", trailing: bytes = b"\x1a") -> bytes:
    descriptor = bytearray(32)
    descriptor[:5] = b"Name\x00"
    descriptor[11] = ord("C")
    descriptor[16] = 8
    header = bytearray(32)
    header[0] = 3
    header[4:8] = struct.pack("<I", 1)
    header[8:10] = struct.pack("<H", 65)
    header[10:12] = struct.pack("<H", 9)
    record = b" " + value.ljust(8)
    return bytes(header) + bytes(descriptor) + b"\x0d" + record + trailing


def shp_bytes(rings=None) -> bytes:
    if rings is None:
        rings = (((43.0, 35.0), (43.0, 35.1), (43.1, 35.1), (43.0, 35.0)),)
    points_by_ring = tuple(point for ring in rings for point in ring)
    points = b"".join(struct.pack("<2d", *point) for point in points_by_ring)
    xs = tuple(point[0] for point in points_by_ring)
    ys = tuple(point[1] for point in points_by_ring)
    bbox = (min(xs), min(ys), max(xs), max(ys))
    part_indexes = []
    next_index = 0
    for ring in rings:
        part_indexes.append(next_index)
        next_index += len(ring)
    content = (
        struct.pack("<i4d2i", 5, *bbox, len(rings), len(points_by_ring))
        + struct.pack("<" + "i" * len(rings), *part_indexes)
        + points
    )
    record = struct.pack(">2i", 1, len(content) // 2) + content
    file_length = (100 + len(record)) // 2
    header = struct.pack(">7i", 9994, 0, 0, 0, 0, 0, file_length)
    header += struct.pack("<2i8d", 1000, 5, *bbox, 0.0, 0.0, 0.0, 0.0)
    return header + record


def with_declared_length(contents: bytearray) -> bytes:
    contents[24:28] = struct.pack(">i", len(contents) // 2)
    return bytes(contents)
