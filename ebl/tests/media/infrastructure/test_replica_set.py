import subprocess
from pathlib import Path
from unittest.mock import Mock

import pytest
from pymongo.errors import ConnectionFailure

from ebl.tests.media.infrastructure import replica_set


@pytest.fixture
def process() -> Mock:
    return Mock(poll=Mock(return_value=None))


def test_ready_poll_retries_connection_failures(
    monkeypatch: pytest.MonkeyPatch, process: Mock
) -> None:
    ready = Mock(side_effect=[ConnectionFailure("Starting"), False, True])
    pause = Mock()
    monkeypatch.setattr(replica_set.time, "sleep", pause)
    replica_set._wait_until_ready(process, ready)
    assert ready.call_count == 3
    assert pause.call_count == 2


def test_ready_poll_rejects_exited_server(process: Mock) -> None:
    process.poll.return_value = 1
    with pytest.raises(RuntimeError, match="exited during startup"):
        replica_set._wait_until_ready(process, Mock())


def test_ready_poll_is_bounded(monkeypatch: pytest.MonkeyPatch, process: Mock) -> None:
    monkeypatch.setattr(replica_set.time, "monotonic", Mock(side_effect=[0, 31]))
    with pytest.raises(RuntimeError, match="did not become ready"):
        replica_set._wait_until_ready(process, Mock())


def test_stopping_exited_server_does_not_signal(process: Mock) -> None:
    process.poll.return_value = 0
    replica_set._stop_server(process)
    process.terminate.assert_not_called()


def test_stopping_server_reaps_process(process: Mock) -> None:
    replica_set._stop_server(process)
    process.terminate.assert_called_once_with()
    process.wait.assert_called_once_with(timeout=replica_set.SHUTDOWN_TIMEOUT)


def test_stopping_unresponsive_server_kills_and_reaps(process: Mock) -> None:
    process.wait.side_effect = [subprocess.TimeoutExpired("mongod", 10), 0]
    replica_set._stop_server(process)
    process.kill.assert_called_once_with()
    assert process.wait.call_count == 2


def test_initialization_failure_stops_process(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, process: Mock
) -> None:
    executable = tmp_path / "mongod"
    executable.touch()
    monkeypatch.setattr(replica_set, "download", Mock(return_value=str(tmp_path)))
    monkeypatch.setattr(replica_set, "Context", Mock())
    monkeypatch.setattr(replica_set.subprocess, "Popen", Mock(return_value=process))
    monkeypatch.setattr(
        replica_set, "_initialize_replica_set", Mock(side_effect=RuntimeError("Failed"))
    )
    with pytest.raises(RuntimeError, match="Failed"):
        with replica_set.replica_set_client():
            pytest.fail("An uninitialized replica set must not be yielded")
    process.terminate.assert_called_once_with()
    process.wait.assert_called_once_with(timeout=replica_set.SHUTDOWN_TIMEOUT)


def test_replica_set_supports_commit_and_abort() -> None:
    with replica_set.replica_set_client() as client:
        collection = client.get_database("media_test_helper").get_collection("records")
        with client.start_session() as session:
            with session.start_transaction():
                collection.insert_one({"_id": "committed"}, session=session)
            session.start_transaction()
            collection.insert_one({"_id": "aborted"}, session=session)
            session.abort_transaction()
        assert collection.find_one({"_id": "committed"}) is not None
        assert collection.find_one({"_id": "aborted"}) is None
