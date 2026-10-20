# Findspot query index readiness

The findspot query slice adds filters on `fragments.archaeology.findspotId`.
The map-data slice also counts fragments by that field. Before enabling
findspot search or `/findspots/map-data` on a deployment, the deployment
owner must record index and query-plan evidence for that database.

Application startup deliberately does not create this index. The regression
test `test_create_indexes_does_not_create_deferred_findspot_index` preserves
that boundary. Index rollout is a separate operator-controlled change.

## Read-only inspection

Use the deployment's approved connection process and a read-only account.
Confirm the cluster and database before running these commands in `mongosh`.
Do not put connection strings or credentials in the evidence record.

```javascript
db.getName();
db.fragments.getIndexes();
```

Look for a completed, visible index whose first key is
`archaeology.findspotId`. The baseline specification is the non-unique,
non-sparse, non-partial ascending index below:

```json
{ "archaeology.findspotId": 1 }
```

An index with this field after another key, a hidden index, an index still
being built, or a partial index is not sufficient evidence by itself.
Review any alternative specification against the actual query plans.
`getIndexes()` can include hidden and in-progress indexes; an index name
alone is not proof of readiness.

## Query-plan evidence

Use a real findspot ID, and a representative set of IDs from the selected
site's artifact mappings. Replace the illustrative IDs below before running
these read-only planner inspections:

```javascript
db.fragments.find({ "archaeology.findspotId": 4242 })
  .explain("queryPlanner");

db.fragments.find({ "archaeology.findspotId": { $in: [4242, 4243] } })
  .explain("queryPlanner");
```

Also inspect the complete aggregation pipelines produced by the deployed
`FragmentPatternMatcher` and map-data count implementation, including the
actual authorization, script and genre filters. Use
`db.fragments.explain("queryPlanner").aggregate(pipeline)` with those
pipelines. A simplified field query alone does not establish readiness for
both routes.

Record whether the winning plan selects the expected index, including
per-shard plans when relevant. An unexpected collection scan remains an
open rollout finding; the planner can reasonably choose one for a very
broad match, so review selectivity and representative workload cost before
acceptance. Do not force a hint merely to make the evidence look indexed.

Planner evidence does not establish latency. Measure representative
endpoint latency and, when approved for the target environment, execution
statistics separately. Include single-ID and multi-ID searches, map counts,
and the supported authorization/script/genre combinations. Compare counts
and results as well as timing.

## Operator-managed migration

If readiness is missing, the deployment owner prepares and approves a
separate index change, including the exact target, index options, resource
budget and maintenance window. Check for an equivalent existing index and
name conflicts first. Do not run this as part of API startup or an artifact
generation/import command.

After that approval, the operator can create the baseline index in the
confirmed database with:

```javascript
db.fragments.createIndex(
  { "archaeology.findspotId": 1 },
  { name: "archaeology_findspot_id_1" }
);
```

This command writes an index and belongs only to the approved migration.
Wait for its completion, repeat the read-only inspection and actual query
plan checks, then record the result before enabling the feature. Keep the
feature rollout blocked while readiness is unresolved. A code deploy or a
passing unit test does not substitute for this database evidence.

If the rollout is reverted, record the application rollback separately.
Do not automatically drop a pre-existing or newly created index: assess
other consumers and obtain a separate approved removal plan if needed.

## Evidence record

Record the deployment/environment identifier, database name, backend commit,
MongoDB version, operator and timestamp. Attach the index specification and
completion status, representative query inputs without sensitive data,
winning plans, and the workload measurements used for acceptance. Record
any migration approval and the final ready/blocked decision.

This document prepares the procedure. It does not certify any live database
or authorize a production index operation.

## MongoDB references

- [Index inspection][indexes]
- [Partial index query coverage][partial]
- [Explain verbosity and plans][explain]
- [Collection aggregation explain][aggregate-explain]

[indexes]: https://www.mongodb.com/docs/manual/reference/method/db.collection.getIndexes/
[partial]: https://www.mongodb.com/docs/manual/core/index-partial/
[explain]: https://www.mongodb.com/docs/manual/reference/method/cursor.explain/
[aggregate-explain]: https://www.mongodb.com/docs/manual/reference/method/db.collection.explain/
