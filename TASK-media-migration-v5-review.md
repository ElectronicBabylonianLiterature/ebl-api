# Media migration v5 review

## Summary

Reviewed PR #787 at `9e2aaefe57bad6d0a39814eecf20d3d2c6b8e175` using
the supplied v5 pipeline. Accepted repairs are independently verified. The
actual persistence parent is integrated without rewriting history. Final
publication and structural-record validation remain coordinator-owned.

## Findings

- E-F1: oversized WebP geometry could reach native decoding before the pixel
  cap. A shared bounded header parser now rejects it first.
- D-01: matching index names and a Boolean lock revision could pass readiness.
  Apply now checks shared canonical index definitions and integer coordination
  state before any registry write. BSON Int64 remains supported.

Historical feedback was separately inventoried and adjudicated; informational
bot notices do not establish a successful review or CI result.

## Severity

Both findings are P2. Corrected behavior is demonstrated on accepted application
inputs in disposable MongoDB. Production incidence and rollout readiness are
not inferred from those tests.

## Reproduction Steps

The unchanged 23-case regression selection changes from 15 expected failures
and eight passing controls to all passing. Final focused verification passes
50 tests with exact expected, collected and JUnit execution IDs and covers
120/120 affected statements. A fresh verifier checks 36 wrong index variants,
Boolean/int/Int64 locks, bounded WebP rejection and valid-image controls.

After actual parent integration, six selected composed tests pass and all four
owned plus eight parent source/test hashes match the reviewed bytes. Required
static, Markdown and whitespace checks pass. Full suites remain delegated to CI.

## Recommendation

Retain the documented preparation, fresh-plan and paused-writer requirements.
This tooling does not resolve ambiguous originals or make the historical audit
an apply manifest. No production access, migration, index preparation,
deployment or PR merge was performed.

## What Has To Be Done

1. Publish the staged merge and retain the final review-record receipt.
2. Let CI and maintainer review complete; remove temporary TASK files before
   merge while preserving README rollout instructions.
3. Merge persistence first, then retarget/integrate this PR onto current master.
4. Separately authorize production preparation, fresh planning and application
   only after the documented operational prerequisites are satisfied.
