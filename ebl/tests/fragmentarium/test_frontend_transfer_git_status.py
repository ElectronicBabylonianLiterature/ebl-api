import pytest

from scripts.maps import frontend_transfer_archive as transfer
from scripts.maps.frontend_transfer_contract import TransferProvenance


@pytest.mark.parametrize(
    ("record", "dirty"),
    [
        ("", False),
        ("? new-source.json\0", True),
        ("1 .M N... 100644 100644 100644 a b source.py\0", True),
    ],
)
def test_nul_git_status_preserves_source_state(
    monkeypatch: pytest.MonkeyPatch, record: str, dirty: bool
) -> None:
    monkeypatch.setattr(
        transfer,
        "_git",
        lambda *args: "# branch.oid " + "a" * 40 + "\0# branch.head master\0" + record,
    )
    assert transfer._git_provenance() == TransferProvenance("a" * 40, dirty)


@pytest.mark.parametrize(
    "status",
    [
        "",
        "# branch.head master\0",
        "# branch.oid (initial)\0",
        "# branch.oid not-a-commit\0",
    ],
)
def test_missing_committed_producer_is_rejected(
    monkeypatch: pytest.MonkeyPatch, status: str
) -> None:
    monkeypatch.setattr(transfer, "_git", lambda *args: status)
    with pytest.raises(ValueError, match="committed producer revision"):
        transfer._git_provenance()
