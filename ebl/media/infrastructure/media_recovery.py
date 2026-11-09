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
from ebl.media.infrastructure.media_documents import load_stored
from ebl.media.infrastructure.media_recovery_uploads import UploadReconciler
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
        if document.get("state") != "deleted":
            continue
        stored = load_stored(document)
        actions.append({"action": "finish-tombstone", "mediaId": document["_id"]})
        if apply:
            for handle in stored.representations.handles:
                store.delete_representation(handle)
            repository.finish_delete(stored)
    reconciler = UploadReconciler(database, store, referenced, apply)
    for request in database.mediaUploadRequests.find({}):
        actions.extend(reconciler.recover(request))
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
