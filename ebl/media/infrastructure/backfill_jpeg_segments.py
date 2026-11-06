from typing import BinaryIO

from PIL import Image

from ebl.media.application.backfill_plan import SourceRejected

SOF_MARKERS = frozenset(
    {0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF}
)


def invalid_jpeg() -> SourceRejected:
    return SourceRejected("blocked", "malformed-original")


def read_marker(content: BinaryIO) -> int:
    if content.read(1) != b"\xff":
        raise invalid_jpeg()
    while value := content.read(1):
        if value != b"\xff":
            return value[0]
    raise invalid_jpeg()


def skip_entropy(content: BinaryIO) -> None:
    while True:
        start = content.tell()
        block = content.read(65_536)
        if not block:
            raise invalid_jpeg()
        offset = 0
        while (position := block.find(b"\xff", offset)) >= 0:
            if position + 1 == len(block):
                following = content.read(1)
                if not following:
                    raise invalid_jpeg()
                marker = following[0]
            else:
                marker = block[position + 1]
            if marker != 0 and marker not in range(0xD0, 0xD8):
                content.seek(start + position)
                return
            offset = position + 2


def exif_evidence(exif: Image.Exif) -> dict[str, str]:
    evidence = {}
    for identifier, name in ((315, "Artist"), (33432, "Copyright")):
        value = exif.get(identifier)
        if isinstance(value, bytes):
            value = value.decode("latin-1")
        if isinstance(value, str) and value.strip("\x00 \n\t"):
            evidence[name] = value.strip("\x00 \n\t")
    return evidence


def read_payload(content: BinaryIO, length: int) -> bytes:
    encoded_length = content.read(2)
    if len(encoded_length) != 2:
        raise invalid_jpeg()
    segment_length = int.from_bytes(encoded_length, "big") - 2
    if segment_length < 0 or content.tell() + segment_length > length:
        raise invalid_jpeg()
    return content.read(segment_length)


def frame_dimensions(payload: bytes) -> tuple[int, int]:
    if len(payload) < 6 or not payload[5] or len(payload) != 6 + 3 * payload[5]:
        raise invalid_jpeg()
    return int.from_bytes(payload[3:5], "big"), int.from_bytes(payload[1:3], "big")


def scan_payload(payload: bytes) -> None:
    if len(payload) < 6 or not payload[0] or len(payload) != 4 + 2 * payload[0]:
        raise invalid_jpeg()


def read_exif(payload: bytes) -> dict[str, str]:
    try:
        exif = Image.Exif()
        exif.load(payload)
        return exif_evidence(exif)
    except (ValueError, OSError, SyntaxError) as error:
        raise SourceRejected("review", "unreadable-attribution-metadata") from error
