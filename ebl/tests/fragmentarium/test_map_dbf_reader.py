from pathlib import Path
import struct

import pytest

from ebl.fragmentarium.application.map_dbf_reader import (
    load_dbf_encoding,
    load_dbf_rows,
)
from ebl.tests.fragmentarium.map_source_test_helpers import dbf_bytes


def _mutated_dbf(offset: int, replacement: bytes) -> bytes:
    contents = bytearray(dbf_bytes())
    end = offset + len(replacement)
    contents[offset:end] = replacement
    return bytes(contents)


def test_load_dbf_encoding_rejects_blank_file(tmp_path: Path):
    path = tmp_path / "source.cpg"
    path.write_text(" \n")

    with pytest.raises(ValueError, match="blank"):
        load_dbf_encoding(path)


@pytest.mark.parametrize(
    "contents, message",
    [
        (_mutated_dbf(0, b"\x04"), "Unsupported DBF version"),
        (_mutated_dbf(8, struct.pack("<H", 64)), "Invalid DBF header length"),
        (dbf_bytes()[:40], "Truncated DBF field descriptor"),
        (_mutated_dbf(32, b"\x00"), "Invalid DBF field descriptor"),
        (_mutated_dbf(48, b"\x00"), "Invalid DBF field descriptor"),
        (_mutated_dbf(64, b"\x00"), "Missing DBF field descriptor terminator"),
        (_mutated_dbf(10, struct.pack("<H", 10)), "Invalid DBF record length"),
        (_mutated_dbf(65, b"*"), "Deleted DBF records"),
        (_mutated_dbf(65, b"X"), "Invalid DBF record marker"),
    ],
)
def test_load_dbf_rows_rejects_invalid_structure(
    tmp_path: Path, contents: bytes, message: str
):
    path = tmp_path / "source.dbf"
    path.write_bytes(contents)

    with pytest.raises(ValueError, match=message):
        load_dbf_rows(path, "ascii")


def test_load_dbf_rows_rejects_duplicate_field_names(tmp_path: Path):
    contents = bytearray(dbf_bytes())
    descriptor = contents[32:64]
    contents[8:10] = struct.pack("<H", 97)
    contents[10:12] = struct.pack("<H", 17)
    contents[64:64] = descriptor
    path = tmp_path / "source.dbf"
    path.write_bytes(bytes(contents))

    with pytest.raises(ValueError, match="Invalid DBF field descriptor"):
        load_dbf_rows(path, "ascii")
