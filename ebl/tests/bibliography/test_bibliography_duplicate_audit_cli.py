import argparse
from pathlib import Path

import pytest

from scripts import bibliography_duplicate_audit


def test_validate_read_target_requires_non_local_opt_in() -> None:
    with pytest.raises(PermissionError, match="allow-non-local-read"):
        bibliography_duplicate_audit.validate_read_target(
            "mongodb://db.example.test:27017",
            "ebldev",
        )


def test_validate_read_target_requires_production_opt_in() -> None:
    with pytest.raises(PermissionError, match="allow-production-read"):
        bibliography_duplicate_audit.validate_read_target(
            "mongodb://localhost:27017",
            "ebl",
        )


def test_validate_read_target_accepts_explicit_remote_production_read() -> None:
    bibliography_duplicate_audit.validate_read_target(
        "mongodb://db.example.test:27017",
        "ebl",
        allow_non_local_read=True,
        allow_production_read=True,
    )


def test_main_rejects_invalid_uri_without_printing_value(capsys) -> None:
    secret_like_uri = "not-a-mongo-uri-with-secret"

    with pytest.raises(SystemExit):
        bibliography_duplicate_audit.main(
            [
                "--mongo-uri",
                secret_like_uri,
                "--database",
                "ebldev",
            ]
        )

    captured = capsys.readouterr()
    assert secret_like_uri not in captured.err
    assert "Invalid MongoDB URI" in captured.err


def test_run_from_args_closes_client_and_reports_counts(monkeypatch, capsys) -> None:
    class FakeClient:
        def __init__(self, mongo_uri: str):
            self.mongo_uri = mongo_uri
            self.closed = False

        def __getitem__(self, database: str) -> str:
            return database

        def close(self) -> None:
            self.closed = True

    created_clients = []

    def fake_mongo_client(mongo_uri: str) -> FakeClient:
        client = FakeClient(mongo_uri)
        created_clients.append(client)
        return client

    def fake_run_audit(database: str, output_dir: Path, overrides_path: Path | None):
        assert database == "ebldev"
        assert output_dir == Path("/tmp/bibliography-audit")
        assert overrides_path is None
        return [object(), object()], [object()]

    monkeypatch.setattr(bibliography_duplicate_audit, "MongoClient", fake_mongo_client)
    monkeypatch.setattr(bibliography_duplicate_audit, "run_audit", fake_run_audit)

    result = bibliography_duplicate_audit.run_from_args(
        argparse.Namespace(
            mongo_uri="mongodb://localhost:27017",
            database="ebldev",
            output_dir=Path("/tmp/bibliography-audit"),
            review_overrides=None,
            allow_non_local_read=False,
            allow_production_read=False,
        )
    )

    captured = capsys.readouterr()
    assert result == 0
    assert created_clients[0].closed is True
    assert "2 candidate pairs, 1 candidate groups" in captured.out
    assert "mongodb://localhost:27017" not in captured.out
