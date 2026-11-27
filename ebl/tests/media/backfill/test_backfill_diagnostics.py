from argparse import Namespace
from contextlib import redirect_stderr
from io import StringIO
from urllib.parse import urlunsplit

import pytest
from pymongo.errors import PyMongoError

from ebl.io.media import backfill

REVIEW_AUTHORITY = "review-user:synthetic-secret"


@pytest.mark.parametrize(
    "error, detail",
    [
        (ValueError("Confirmation rejected"), "Confirmation rejected"),
        (OSError(28, "No space left"), "No space left"),
        (PyMongoError("private driver detail"), "PyMongoError"),
    ],
)
def test_stop_reports_target_without_credentials(
    monkeypatch: pytest.MonkeyPatch, error: Exception, detail: str
) -> None:
    uri = urlunsplit(("mongodb", "test-user:test-password@LOCALHOST:27017", "", "", ""))
    monkeypatch.setenv("MEDIA_DIAGNOSTIC_URI", uri)

    def fail(_arguments: Namespace) -> dict:
        raise error

    monkeypatch.setattr(backfill, "execute", fail)
    with StringIO() as output, redirect_stderr(output):
        status = backfill.main(
            [
                "prepare-indexes",
                "--database",
                "diagnostic-test",
                "--confirm-database",
                "diagnostic-test",
                "--uri-env",
                "MEDIA_DIAGNOSTIC_URI",
            ]
        )
        message = output.getvalue()
    assert status == 1
    assert '"endpoint": "localhost:27017"' in message
    assert '"database": "diagnostic-test"' in message
    assert detail in message
    assert "test-user" not in message
    assert "test-password" not in message
    assert "private driver detail" not in message


@pytest.mark.parametrize(
    "uri",
    [
        None,
        "https://user:secret@invalid",
        "mongodb://[",
        urlunsplit(("mongodb", REVIEW_AUTHORITY, "/unescaped@localhost:27017", "", "")),
        urlunsplit(("mongodb", REVIEW_AUTHORITY, "", "unescaped@localhost:27017", "")),
        urlunsplit(("mongodb", REVIEW_AUTHORITY, "", "", "unescaped@localhost:27017")),
        urlunsplit(("mongodb", REVIEW_AUTHORITY, "", "", "")),
    ],
)
def test_unavailable_endpoint_does_not_hide_original_stop(
    monkeypatch: pytest.MonkeyPatch, uri: str | None
) -> None:
    if uri is None:
        monkeypatch.delenv("MEDIA_DIAGNOSTIC_URI", raising=False)
    else:
        monkeypatch.setenv("MEDIA_DIAGNOSTIC_URI", uri)
    with StringIO() as output, redirect_stderr(output):
        status = backfill.main(
            [
                "prepare-indexes",
                "--database",
                "diagnostic-test",
                "--confirm-database",
                "different",
                "--uri-env",
                "MEDIA_DIAGNOSTIC_URI",
            ]
        )
        message = output.getvalue()
    assert status == 1
    assert '"endpoint": "<unavailable>"' in message
    assert '"database": "diagnostic-test"' in message
    assert "ValueError" in message
    assert "Database confirmation does not match the target." in message
    assert "secret" not in message
    assert "review-user" not in message


def test_malformed_host_list_has_no_display_endpoint(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("MEDIA_DIAGNOSTIC_URI", "mongodb://localhost:27017,")
    assert backfill.display_target(
        Namespace(uri_env="MEDIA_DIAGNOSTIC_URI", database="diagnostic-test")
    ) == {"endpoint": "<unavailable>", "database": "diagnostic-test"}
