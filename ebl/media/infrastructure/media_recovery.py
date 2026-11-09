"""Offline, explicit recovery after draining API traffic and active binary readers.

Nothing here runs at startup. The operator must stop/drain *all* media writers
and readers before applying recovery. Dry runs are the default.
"""

import argparse
import json
import os

from pymongo import MongoClient

from ebl.media.infrastructure.grid_fs_media_representation_store import (
    GridFsMediaRepresentationStore,
)
from ebl.media.infrastructure.media_documents import load_handle, load_stored
from ebl.media.infrastructure.mongo_media_management import (
    MongoMediaManagementRepository,
)


def recover_media(database, *, apply=False, quiescent=False):
    if apply and not quiescent:
        raise ValueError(
            "Applying recovery requires all media readers/writers drained (--quiescent)."
        )
    repository = MongoMediaManagementRepository(database)
    store = GridFsMediaRepresentationStore(database)
    documents = list(database.media.find({}))
    referenced = {
        handle.value
        for document in documents
        for handle in load_stored(document).representations.handles
    }
    actions = []
    for document in documents:
        if document.get("state") == "deleted":
            stored = load_stored(document)
            actions.append({"action": "finish-tombstone", "mediaId": document["_id"]})
            if apply:
                for handle in stored.representations.handles:
                    store.delete_representation(handle)
                repository.finish_delete(stored)
    for request in database.mediaUploadRequests.find({}):
        current = database.media.find_one({"_id": request["mediaId"]})
        # This also reconciles stale generations from a failed attempt followed by
        # a successful retry. Committed reservations may still own such orphans.
        unreferenced = tuple(
            load_handle(record["handle"])
            for record in database.mediaFiles.find(
                {
                    "handle.mediaId": request["mediaId"],
                    "ownership": "owned",
                    "deleted": {"$ne": True},
                }
            )
            if record["handle"]["value"] not in referenced
        )
        if current is not None:
            # Preserve uncertain commits and retained tombstones. Never infer absence
            # from public queries, which deliberately omit unpublished/deleted items.
            if unreferenced:
                actions.append(
                    {
                        "action": "reconcile-orphans",
                        "requestId": request["_id"],
                        "count": len(unreferenced),
                    }
                )
                if apply:
                    for handle in unreferenced:
                        store.delete_representation(handle)
            elif request["state"] != "committed":
                actions.append(
                    {"action": "preserve-existing", "requestId": request["_id"]}
                )
            continue
        if request["state"] == "committed":
            # A removed upload keeps its idempotency history and cannot reappear.
            if unreferenced:
                actions.append(
                    {
                        "action": "reconcile-orphans",
                        "requestId": request["_id"],
                        "count": len(unreferenced),
                    }
                )
                if apply:
                    for handle in unreferenced:
                        store.delete_representation(handle)
            continue
        actions.append({"action": "recover-incomplete", "requestId": request["_id"]})
        if apply:
            # Include registry entries whose write crashed before the journal callback.
            for handle in unreferenced:
                store.delete_representation(handle)
            database.mediaUploadRequests.update_one(
                {
                    "_id": request["_id"],
                    "lease": request["lease"],
                    "state": request["state"],
                },
                {"$set": {"state": "failed", "recovered": True}},
            )
    return actions


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", required=True)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--quiescent", action="store_true")
    args = parser.parse_args()
    with MongoClient(os.environ["MONGODB_URI"]) as client:
        print(
            json.dumps(
                recover_media(
                    client[args.database], apply=args.apply, quiescent=args.quiescent
                ),
                indent=2,
            )
        )


if __name__ == "__main__":
    main()
