from __future__ import annotations

import codecs
from pathlib import Path
import struct
from typing import BinaryIO

DbfField = tuple[str, int]


def load_dbf_encoding(path: Path) -> str:
    try:
        encoding = path.read_text(encoding="utf-8-sig").strip()
    except (OSError, UnicodeError) as error:
        raise ValueError(f"Cannot read required DBF encoding file {path}.") from error
    if not encoding:
        raise ValueError(f"DBF encoding file {path} is blank.")
    try:
        codecs.lookup(encoding)
    except LookupError as error:
        raise ValueError(f"Unknown DBF encoding {encoding!r} in {path}.") from error
    return encoding


def load_dbf_rows(path: Path, encoding: str) -> tuple[dict[str, str], ...]:
    with path.open("rb") as file_:
        record_count, field_count, record_length = _read_dbf_header(file_, path)
        fields = _read_dbf_fields(file_, path, field_count)
        if record_length != 1 + sum(length for _, length in fields):
            raise ValueError(f"Invalid DBF record length in {path}.")
        rows = tuple(
            _decode_dbf_record(
                _read_dbf_record(file_, path, record_length), fields, encoding
            )
            for _ in range(record_count)
        )
        if file_.read() not in (b"", b"\x1a"):
            raise ValueError(f"Unexpected trailing bytes in {path}.")
    return rows


def _read_dbf_header(file_: BinaryIO, path: Path) -> tuple[int, int, int]:
    header = file_.read(32)
    if len(header) != 32:
        raise ValueError(f"Truncated DBF header in {path}.")
    if header[0] != 3:
        raise ValueError(f"Unsupported DBF version in {path}.")
    record_count = struct.unpack("<I", header[4:8])[0]
    header_length, record_length = struct.unpack("<2H", header[8:12])
    if header_length < 33 or (header_length - 33) % 32:
        raise ValueError(f"Invalid DBF header length in {path}.")
    return record_count, (header_length - 33) // 32, record_length


def _read_dbf_fields(
    file_: BinaryIO, path: Path, field_count: int
) -> tuple[DbfField, ...]:
    fields: list[DbfField] = []
    for _ in range(field_count):
        fields.append(_read_dbf_field(file_, path, fields))
    if file_.read(1) != b"\x0d":
        raise ValueError(f"Missing DBF field descriptor terminator in {path}.")
    return tuple(fields)


def _read_dbf_field(
    file_: BinaryIO, path: Path, existing_fields: list[DbfField]
) -> DbfField:
    descriptor = file_.read(32)
    if len(descriptor) != 32:
        raise ValueError(f"Truncated DBF field descriptor in {path}.")
    name = descriptor[:11].split(b"\x00", 1)[0].decode("ascii")
    length = descriptor[16]
    if not name or not length or any(name == field for field, _ in existing_fields):
        raise ValueError(f"Invalid DBF field descriptor in {path}.")
    return name, length


def _read_dbf_record(file_: BinaryIO, path: Path, record_length: int) -> bytes:
    record = file_.read(record_length)
    if len(record) != record_length:
        raise ValueError(f"Truncated DBF record in {path}.")
    if record[:1] == b"*":
        raise ValueError(f"Deleted DBF records are unsupported in {path}.")
    if record[:1] != b" ":
        raise ValueError(f"Invalid DBF record marker in {path}.")
    return record


def _decode_dbf_record(
    record: bytes, fields: tuple[DbfField, ...], encoding: str
) -> dict[str, str]:
    row = {}
    position = 1
    for name, length in fields:
        end = position + length
        row[name] = record[position:end].decode(encoding).strip()
        position = end
    return row
