# TASK-735-finding5 TODO — Explain the redirect-stub rule decision

Goal: explain Finding 5 in plain terms so a decision can be made. No code
change unless the decision is given.

## Steps

- [x] 1. Create this TODO and `TASK-735-finding5-log.md` first
- [x] 2. Re-read the current rule in `realia_stub_filter.py` and state it
      exactly
- [x] 3. Build the full truth table of entry shapes against a real MongoDB:
      0, 1, 2 cross-references, with and without own content
- [x] 4. Check what ebl-frontend actually renders for an entry that has
      only cross-references — this decides whether such a page deserves a
      sitemap URL
- [x] 5. Identify any additional shapes the rule handles badly (e.g. the
      completely empty entry)
- [x] 6. Write the explanation with a concrete recommendation
- [x] 7. Make NO commits

## Notes

- No commit or push; the user's commit authorisation was single-use and
  has been spent.
