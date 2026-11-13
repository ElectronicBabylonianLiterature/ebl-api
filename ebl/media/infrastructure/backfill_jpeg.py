from typing import BinaryIO

from ebl.media.infrastructure.backfill_jpeg_segments import (
    SOF_MARKERS,
    frame_dimensions,
    invalid_jpeg,
    read_exif,
    read_marker,
    read_payload,
    scan_payload,
    skip_entropy,
)


class JpegInspection:
    def __init__(self) -> None:
        self.width = 0
        self.height = 0
        self.scanned = False
        self.evidence: dict[str, str] = {}

    def inspect_segment(self, marker: int, payload: bytes, content: BinaryIO) -> None:
        if marker in SOF_MARKERS:
            self.width, self.height = frame_dimensions(payload)
        elif marker == 0xE1 and payload.startswith(b"Exif\x00\x00"):
            self.evidence.update(read_exif(payload))
        elif marker == 0xDA:
            scan_payload(payload)
            self.scanned = True
            skip_entropy(content)

    def result(self, content: BinaryIO) -> tuple[int, int, dict[str, str]]:
        if not self.scanned or not self.width or not self.height:
            raise invalid_jpeg()
        content.seek(0)
        return self.width, self.height, self.evidence


def inspect_jpeg(content: BinaryIO, length: int) -> tuple[int, int, dict[str, str]]:
    content.seek(0)
    if content.read(2) != b"\xff\xd8":
        raise invalid_jpeg()
    inspection = JpegInspection()
    while content.tell() < length:
        marker = read_marker(content)
        if marker == 0xD9:
            return inspection.result(content)
        if marker in {0, 0xD8} or 0xD0 <= marker <= 0xD7:
            raise invalid_jpeg()
        if marker != 1:
            inspection.inspect_segment(marker, read_payload(content, length), content)
    raise invalid_jpeg()
