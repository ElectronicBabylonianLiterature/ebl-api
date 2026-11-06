from typing import BinaryIO


def _dimensions(chunk_type: bytes, payload: bytes) -> tuple[int, int]:
    if chunk_type == b"VP8X" and len(payload) >= 10:
        return (
            int.from_bytes(payload[4:7], "little") + 1,
            int.from_bytes(payload[7:10], "little") + 1,
        )
    if chunk_type == b"VP8L" and len(payload) >= 5 and payload[0] == 0x2F:
        bits = int.from_bytes(payload[1:5], "little")
        if bits >> 29 == 0:
            return (bits & 0x3FFF) + 1, ((bits >> 14) & 0x3FFF) + 1
    if (
        chunk_type == b"VP8 "
        and len(payload) >= 10
        and payload[0] & 1 == 0
        and payload[3:6] == b"\x9d\x01\x2a"
    ):
        width = int.from_bytes(payload[6:8], "little") & 0x3FFF
        height = int.from_bytes(payload[8:10], "little") & 0x3FFF
        if width and height:
            return width, height
    raise ValueError("Malformed WebP geometry header.")


def webp_dimensions(content: BinaryIO) -> tuple[int, int] | None:
    position = content.tell()
    try:
        content.seek(0)
        header = content.read(30)
        if not header.startswith(b"RIFF") or header[8:12] != b"WEBP":
            return None
        length = content.seek(0, 2)
        declared_length = int.from_bytes(header[4:8], "little") + 8
        chunk_length = int.from_bytes(header[16:20], "little")
        if (
            len(header) < 20
            or declared_length > length
            or declared_length % 2
            or 20 + chunk_length + chunk_length % 2 > declared_length
        ):
            raise ValueError("Malformed WebP container header.")
        payload = header[20:]
        return _dimensions(header[12:16], payload[:chunk_length])
    finally:
        content.seek(position)
