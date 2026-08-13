# TASK-741-recheck Work Log

Branch: `fix-afo-register-texts-numbers-split`
Question: does anything remain unaddressed on PR #741?

## 2026-08-13

### Step 0 — Task artefacts

Created `TASK-741-recheck-todo.md` and this log before starting, per the
task-tracking hard gate. This is a third distinct task; the review's and the
fix's files do not carry forward.

### Step 1 — Self-review of the TASK-741-fix changes

Nobody has reviewed the code I wrote, so I re-derived its bounds and measured
them rather than trusting the earlier estimate.

**True post-fix worst case.** My earlier 4.24 MB figure used 4-byte characters,
which under-uses a *byte* budget. ASCII is the real worst case: it buys the most
characters per byte, hence the most token content per candidate. Measured with
`bson.encode` at 24 tokens and exactly `MAX_QUERY_BYTES` bytes per query:

- 10,000 candidates, **5,378,905 bytes = 5.13 MB**
- under the 16 MB BSON limit with **3.1x headroom**

So the fix holds under the genuine worst case, not just the one I first tried.

**`MAX_JSON_ESCAPE_EXPANSION = 6`.** Checked empirically over the ASCII range,
`U+2028`, `U+FFFD`, `U+12000` and `U+10FFFF`: the maximum bytes-out per byte-in
under `json.dumps` is exactly **6.0** (an ASCII character escaped as `\u00XX`).
The constant is right, not merely conservative.

**No legitimate request is rejected.** 1,000 maximum-size ASCII queries encode
to 504,000 bytes against a `MAX_REQUEST_BYTES` of 3,003,002 — roughly 6x margin.

**`Content-Length` cannot smuggle a larger body.** Falcon reads through
`bounded_stream`, capped at the declared length, so under-declaring truncates
the body and fails JSON parsing (400) rather than sneaking past the guard.
Over-declaring is what the new guard rejects.

Result: **no defect found in the fix.**

### Step 2 — The single-token / empty-field question, chased to a conclusion

This was the one loose end from the review: `candidate_splits` never yields an
empty `text` or `textNumber`, so a single-token query can match nothing. The
question was whether the **old** code's concat fallback did match such records —
if so, this PR would carry an unflagged behaviour regression.

Read the old implementation from `origin/master`:

- `split_text_and_number` returned `None` for a single-token query, and also for
  an empty side.
- When *any* query in the batch failed to split, `_build_indexed_query` returned
  `None` and the whole batch went through `_build_fallback_pipeline`, which
  matched `{"$concat": ["$text", " ", "$textNumber"]}` against the query.

The separator is unconditional, so a record with an empty `textNumber` concatenates
to `"Solo "` — with a trailing space — and can never equal a normalized query.
The old code could not match those records either.

Rather than rest on that reading, I ran a **differential test** against a real
mongo, seeding the edge cases (empty `textNumber`, empty `text`, trailing space
inside `text`, double space inside `textNumber`, ambiguous pairs, decoys) and
comparing the new implementation against both old semantics over 15 queries:

- **mismatches vs the old concat semantics: 0**
- **results the old indexed path found that the new code loses: 0**

Conclusion: **not a regression.** The new logic is exactly equivalent to the old
concat semantics and a strict superset of the old indexed path. No fix needed.

Worth recording but not fixing: a record with an empty `text` or `textNumber` is
unreachable through this endpoint, in the old code and the new. That is a
pre-existing property of the concat contract, not something this PR introduced,
and changing it would change the endpoint's contract.

### Step 3 — GitHub state re-checked

- Unresolved review threads: **1** — Fabdulla1's `3776566330` on
  `afo_register_records.py:25`, which the F-1 fix addresses. It can only be
  resolved on GitHub after the change is pushed; no GitHub write was performed.
- No review, inline or conversation comment newer than the last check.
- CI: nothing failing.

### Step 4 — Outcome

**No remaining findings to fix.** No code was changed in this task; the working
tree still holds exactly the TASK-741-fix changes. Gates were therefore not
re-run for code, except `task lint-md` for the new markdown.

Left deliberately undone, and why:

1. Resolving thread `3776566330` — requires a GitHub write and a push, neither
   of which is authorized.
2. The chunked-transfer-encoding gap in F-2 — needs a body limit at the WSGI
   server or reverse proxy; API-wide and outside this endpoint.
3. Removing the `TASK-741*.md` scaffolding — must happen before merge.
