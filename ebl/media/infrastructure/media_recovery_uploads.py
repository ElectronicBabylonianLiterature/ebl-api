"""Reconcile upload reservations only after the operator has drained readers."""

from ebl.media.infrastructure.media_documents import load_handle


class UploadReconciler:
    def __init__(self, database, store, referenced, apply):
        self.database = database
        self.store = store
        self.referenced = referenced
        self.apply = apply

    def recover(self, request):
        current = self.database.media.find_one({"_id": request["mediaId"]})
        handles = self._unreferenced(request)
        # Committed requests can own stale generations from failed earlier attempts.
        # Existing metadata and committed idempotency history must remain intact.
        if current is not None or request["state"] == "committed":
            return self._preserve_current(request, handles, current is not None)
        self._delete_handles(handles)
        if self.apply:
            self._reset_request(request)
        return [{"action": "recover-incomplete", "requestId": request["_id"]}]

    def _unreferenced(self, request):
        records = self.database.mediaFiles.find(
            {
                "handle.mediaId": request["mediaId"],
                "ownership": "owned",
                "deleted": {"$ne": True},
            }
        )
        return tuple(
            load_handle(record["handle"])
            for record in records
            if record["handle"]["value"] not in self.referenced
        )

    def _preserve_current(self, request, handles, current_exists):
        if handles:
            self._delete_handles(handles)
            return [
                {
                    "action": "reconcile-orphans",
                    "requestId": request["_id"],
                    "count": len(handles),
                }
            ]
        if current_exists and request["state"] != "committed":
            return [{"action": "preserve-existing", "requestId": request["_id"]}]
        return []

    def _delete_handles(self, handles):
        if self.apply:
            for handle in handles:
                self.store.delete_representation(handle)

    def _reset_request(self, request):
        self.database.mediaUploadRequests.update_one(
            {
                "_id": request["_id"],
                "lease": request["lease"],
                "state": request["state"],
            },
            {"$set": {"state": "failed", "recovered": True}},
        )
