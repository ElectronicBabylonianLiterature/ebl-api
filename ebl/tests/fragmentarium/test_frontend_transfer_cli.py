from pathlib import Path

from scripts.maps import build_frontend_transfer_archive as cli
from scripts.maps import frontend_transfer_archive as transfer


def test_default_output_is_outside_repo_and_repeatable(tmp_path, monkeypatch):
    monkeypatch.setattr(cli.tempfile, "gettempdir", lambda: str(tmp_path))

    def fake_git(*args: str) -> str:
        if args[0] == "status":
            return ""
        return "a" * 40

    monkeypatch.setattr(transfer, "_git", fake_git)
    output = Path(tmp_path) / "map-multi-site-canonical-artifacts.tar.gz"

    assert cli._parse_args([]).output == output
    assert cli.main([]) == 0
    first = output.read_bytes()
    assert cli.main([]) == 0
    assert output.read_bytes() == first
