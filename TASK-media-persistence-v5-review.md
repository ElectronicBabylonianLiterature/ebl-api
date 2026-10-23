# Media persistence v5 review

## Scope and corrections

Reviewed PR #785 at `48b27b008d48bdf85b220839c060ed4892d6cfef` with
the user-supplied v5 pipeline. Six independent discovery roles were followed by
separate adjudication, implementation and fresh verification.

- E-F1: inspect WebP geometry with bounded header reads before native decoder
  creation. This closes a pre-validation allocation path for oversized images.
- E-F2: decode bounded JPEGs before storage so truncated scans and missing EOI
  markers cannot enter the ready registry.
- D-01 prerequisite: share canonical index definitions between preparation and
  the migration readiness checks in PR #787, including exact keys, uniqueness
  and simple collation.

The implementation preserves borrowed legacy ownership. Explicit deletion of
an old owned handle can still interrupt an existing reader. That separately
accepted cleanup limitation is not fixed here; current HTTP routes are read
only and the migration creates records. SVG ingestion remains rejected under
the accepted raster-only scope.

## Verification

The original image regressions reproduced three failures while valid controls
passed. The corrected focused selection passes 99 cases and covers all 302
statements in the five affected production modules. Whole Pyre, Pyright, mypy,
Ruff, Flake8, Qlty and Markdown checks pass.

A fresh verifier independently confirmed that truncated JPEGs create no
registry, GridFS file or chunk records, while valid JPEGs round-trip. Static
and animated oversized WebP controls are rejected before decoder entry. A
separate bounded native-allocation probe preserves the valid animated control.
These checks use disposable local MongoDB, never production.

Full suites remain delegated to CI. No CI result or production rollout is
claimed. Exact commands, source hashes, negative controls and final publication
receipts are retained in the coordinator's portable review record.

## What Has To Be Done

1. Let CI complete required full suites and obtain maintainer approval.
2. Merge this persistence prerequisite before PRs #786 and #787. Those branches
   must carry this exact parent revision and retain their own verification.
3. Remove temporary TASK files before merge, retaining permanent README and
   PR rollout guidance.
4. Perform index preparation and migration only through the separately
   authorized, reviewed rollout. This review performs neither operation.
