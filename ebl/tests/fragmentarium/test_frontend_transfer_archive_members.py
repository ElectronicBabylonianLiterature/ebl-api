import io
import tarfile

import pytest

from scripts.maps import frontend_transfer_archive as transfer


def test_archive_member_names_must_be_basenames() -> None:
    stream = io.BytesIO()
    with tarfile.open(fileobj=stream, mode="w") as archive:
        with pytest.raises(ValueError, match="must be a basename"):
            transfer._add_member(archive, "../escape", b"payload")
