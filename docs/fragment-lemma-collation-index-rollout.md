# Fragment lemma search: collated index rollout

## Motivation and scope

Fragment lemma searches use the multikey field
`text.lines.content.uniqueLemma` with the query collation:

```javascript
{ locale: "en", numericOrdering: true, alternate: "shifted" }
```

The existing single-field lemma index has simple collation on the test collection.
On an isolated MongoDB 7.0 instance, the representative query performed a
`COLLSCAN` with the search collation and an `IXSCAN` without it. Production
index metadata and query plans have **not** been verified. Query-plan
compatibility does not establish a latency improvement on production-sized data.

The new index is named `fragment_unique_lemma_en_numeric_shifted`. It is
additive and retains the simple-collation index for callers using that
collation. Search semantics, including collation, sorting, exact counts,
authorization, and pagination, are unchanged.

## Safe deployment boundary

`create_fragmentarium_routes()` calls `create_indexes()` during **every API
startup**. The new index is **deliberately not** in that startup method.
`MongoFragmentRepository.create_collated_lemma_index()` is an explicit,
idempotent migration helper; neither importing nor deploying this code
builds the new production index.

A production index build requires a separately approved operator action,
with capacity, disk space, replication lag and maintenance-window planning.
Do **not** enable it automatically on an API restart.

## Before the build (read-only)

1. Confirm the application database, MongoDB version, replica-set topology,
   effective `fragments` collection default collation, and actual index
   definitions on the intended deployment. Use authorized TLS credentials,
   not a default unauthenticated `mongosh` connection.
2. Inspect `db.fragments.getIndexes()`. Check for an existing index of the
   same name, field, and collation; stop rather than dropping/replacing an
   unexpected index.
3. Use the application's `PatternMatcher` pipeline for representative AND,
   OR, LINE and PHRASE searches and `explain("queryPlanner")` with the
   application's exact collation. Record whether the winning plan uses
   `COLLSCAN`, index names and eligibility, and compare representative
   rare/common lemmas. Do not run `executionStats` on production.
4. Establish a baseline for API p50/p95, cancellations (499), MongoDB
   utilization, query mix and replication lag. The synthetic-data plan
   result alone is not production acceptance evidence.

## Approved, scheduled index build (write action)

Only after explicit approval and a successful staging rehearsal, execute
**once** as an authorized database administrator against the correct
application database, using the deployment's existing secure TLS connection.
This is an illustrative `mongosh` command, **not** an automatic startup hook:

```javascript
db.getSiblingDB("<verified-app-database>").fragments.createIndex(
  { "text.lines.content.uniqueLemma": 1 },
  {
    name: "fragment_unique_lemma_en_numeric_shifted",
    collation: { locale: "en", numericOrdering: true, alternate: "shifted" }
  }
)
```

Or invoke `MongoFragmentRepository.create_collated_lemma_index()` in a
separate, authorized maintenance process configured to use the same
database. Do not run either operation on an unverified replica or with
hardcoded credentials. The index build may consume significant CPU, disk
and I/O on each replica-set member; monitor progress and replication lag.

## Acceptance (read-only)

- Verify the named index appears with the exact key and collation on the
  appropriate replica-set members; the original simple index remains.
- Re-run the **unhinted** real `PatternMatcher` pipeline with
  `explain("queryPlanner")`, checking that a representative selective
  lemma lookup actually chooses an index-supported plan. The isolated
  automated test uses a hint to verify the access path is possible;
  it does **not** guarantee the optimizer chooses it for every query.
- Compare search results, order, permissions, paginated totals and counts
  against the baseline for AND/OR/LINE/PHRASE and punctuation/whitespace
  cases. Verify rare and common lemmas separately.
- Measure sustained request latency (p50/p95/p99), 499/429/5xx rates,
  index usage, memory, I/O and replica lag against comparable traffic.
  Common lemmas can still be slow due to unwind, sort and exact count.

## Recovery

If the build causes significant resource pressure, follow the MongoDB
operator's documented abort/recovery process and coordinate with the
database administrator. Do not automatically drop either index during
an API rollback. Removing the new index, if later approved, is a separate
explicit database write; keep the original simple index intact. No
application behavior change is required to revert this PR's shared
collation constant or migration helper.

This change alone does not address full-match sort/count overhead,
`/api/texts` serialization, or request queueing; measure those separately.
