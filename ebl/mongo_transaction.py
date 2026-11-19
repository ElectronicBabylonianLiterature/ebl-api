from typing import Callable, TypeVar

from pymongo import MongoClient, ReadPreference
from pymongo.client_session import ClientSession
from pymongo.read_concern import ReadConcern
from pymongo.write_concern import WriteConcern

Result = TypeVar("Result")


def supports_transactions(client: MongoClient) -> bool:
    topology = client.admin.command("hello")
    return bool(topology.get("setName")) or topology.get("msg") == "isdbgrid"


def run_in_transaction(
    client: MongoClient, operation: Callable[[ClientSession], Result]
) -> Result:
    with client.start_session() as session:
        return session.with_transaction(
            operation,
            read_concern=ReadConcern("snapshot"),
            write_concern=WriteConcern("majority"),
            read_preference=ReadPreference.PRIMARY,
        )
