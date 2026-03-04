# TASK-676 Work Log

## 2026-03-03
- Updated `.github/instructions/copilot.instructions.md` with a generic rule for field-name mismatches: backend schema is authoritative; clients should align; backend aliases require explicit backward-compatibility request.
- Hardened `POST /words/create-proper-noun` in `ebl/dictionary/web/words.py` to reject invalid creation states and return `500` instead of `201` with invalid payloads.
- Added endpoint tests in `ebl/tests/dictionary/test_create_proper_noun.py` for required success payload shape (`_id`, `lemma`, `pos`) and for `500` when created id/payload is invalid.
