import os
import socket
import subprocess
import time
from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Callable, Iterator

from pymongo import MongoClient
from pymongo.errors import PyMongoError
from pymongo_inmemory.context import Context
from pymongo_inmemory.downloader import download


STARTUP_TIMEOUT = 30.0
SHUTDOWN_TIMEOUT = 10.0
REPLICA_SET_NAME = "media-tests"


def _available_port() -> int:
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        return int(listener.getsockname()[1])


def _wait_until_ready(
    process: subprocess.Popen[bytes], ready: Callable[[], bool]
) -> None:
    deadline = time.monotonic() + STARTUP_TIMEOUT
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError("Temporary MongoDB replica set exited during startup.")
        try:
            if ready():
                return
        except PyMongoError:
            pass
        time.sleep(0.1)
    raise RuntimeError("Temporary MongoDB replica set did not become ready in time.")


def _stop_server(process: subprocess.Popen[bytes]) -> None:
    if process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=SHUTDOWN_TIMEOUT)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=SHUTDOWN_TIMEOUT)


def _initialize_replica_set(process: subprocess.Popen[bytes], port: int) -> None:
    client: MongoClient
    with MongoClient(
        "127.0.0.1",
        port,
        directConnection=True,
        serverSelectionTimeoutMS=1000,
        socketTimeoutMS=1000,
        connectTimeoutMS=1000,
    ) as client:
        _wait_until_ready(process, lambda: bool(client.admin.command("ping")["ok"]))
        client.admin.command(
            "replSetInitiate",
            {
                "_id": REPLICA_SET_NAME,
                "members": [{"_id": 0, "host": f"127.0.0.1:{port}"}],
            },
        )
        _wait_until_ready(
            process,
            lambda: bool(client.admin.command("hello").get("isWritablePrimary")),
        )


@contextmanager
def replica_set_client() -> Iterator[MongoClient]:
    client: MongoClient
    executable = Path(download(Context())) / "mongod"
    executable.chmod(executable.stat().st_mode | 0o100)
    port = _available_port()
    with TemporaryDirectory(prefix="ebl-media-tests-") as directory:
        with (Path(directory) / "mongod.log").open("wb") as output:
            process = subprocess.Popen(
                [
                    os.fspath(executable),
                    "--bind_ip",
                    "127.0.0.1",
                    "--port",
                    str(port),
                    "--replSet",
                    REPLICA_SET_NAME,
                    "--nounixsocket",
                    "--dbpath",
                    directory,
                    "--wiredTigerCacheSizeGB",
                    "0.25",
                    "--setParameter",
                    "diagnosticDataCollectionEnabled=false",
                ],
                stdout=output,
                stderr=subprocess.STDOUT,
            )
            try:
                _initialize_replica_set(process, port)
                with MongoClient(
                    "127.0.0.1",
                    port,
                    replicaSet=REPLICA_SET_NAME,
                    serverSelectionTimeoutMS=1000,
                ) as client:
                    yield client
            finally:
                _stop_server(process)
