# CRLF Line Ending Fix - Detailed Todo

## Overview

A PR merged recently changed line endings across 609 files from LF to CRLF (or vice versa), which broke Git blame history and rendered GitLens useless. This todo tracks the steps to mitigate the damage and prevent future occurrences.

---

## Step 1: Identify CRLF Commit Hash

**Objective:** Find the commit hash of the PR that introduced the CRLF changes

**Details:**

- Look through recent commits on the `master` branch
- Identify the commit with ~609 modified files but no actual code changes
- This is typically a recent commit from your colleague's backend optimization PR
- Document the exact commit hash (40-character SHA)

**Command to use:**

```bash
git log --oneline -20 master
# or
git log --oneline --all -50 | grep -i "backend\|optim\|crlf"
```

**Expected outcome:** Exact commit hash noted (e.g., `a1b2c3d4...`)

---

## Step 2: Create .git-blame-ignore-revs File

**Objective:** Create a configuration file that tells Git to ignore the CRLF commit during blame operations

**Details:**

- Create a new file in the repository root: `.git-blame-ignore-revs`
- This file contains a list of commit hashes that should be ignored when running `git blame`
- GitLens automatically respects this file
- Format: One commit hash per line, with optional comments

**File location:** `/workspaces/ebl-api/.git-blame-ignore-revs`

**Expected outcome:** File created with proper formatting

---

## Step 3: Add Commit Hash to Ignore File

**Objective:** Reference the CRLF commit in the ignore file

**Details:**

- Insert the commit hash identified in Step 1
- Add a comment explaining why it's being ignored
- Format: `# CRLF line ending normalization` followed by the hash

**Example:**

```
# CRLF/LF line ending normalization commit
a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0
```

**Expected outcome:** `.git-blame-ignore-revs` contains the commit hash with explanation

---

## Step 4: Configure Git Blame Settings

**Objective:** Tell Git to use the blame ignore file for all blame operations

**Details:**

- Run git config command to set `blame.ignoreRevsFile`
- This ensures Git (and GitLens) respects the ignore file
- Can be set locally or globally; recommend locally for this repo

**Command to run:**

```bash
git config blame.ignoreRevsFile .git-blame-ignore-revs
```

**Verify with:**

```bash
git config blame.ignoreRevsFile
```

**Expected outcome:** Git will use `.git-blame-ignore-revs` for all blame commands

---

## Step 5: Create .gitattributes File

**Objective:** Enforce consistent line endings to prevent future CRLF disasters

**Details:**

- Create `.gitattributes` in the repository root
- Enforce LF line endings for all text files (standard for backend projects)
- This prevents autocrlf issues across different developer environments
- Use `text=auto eol=lf` for strict control

**File location:** `/workspaces/ebl-api/.gitattributes`

**Recommended content:**

```
* text=auto eol=lf
*.py text eol=lf
*.md text eol=lf
*.yml text eol=lf
*.yaml text eol=lf
*.json text eol=lf
```

**Expected outcome:** `.gitattributes` created with consistent line ending rules

---

## Step 6: Split Normalization into Separate PR

**Objective:** Keep the line-ending normalization in its own PR and keep the config/docs PR clean

**Details:**

- Create a normalization-only branch from `master`
- Cherry-pick the normalization commit onto that branch
- Open a PR and merge with a regular merge (not squash)
- Ensure the config/docs PR does not include the normalization commit
- Update `.git-blame-ignore-revs` and documentation with the new normalization hash

**Commands to use:**

```bash
git checkout master
git checkout -b crlf-normalization
git cherry-pick 7b57f250
git push -u origin crlf-normalization
```

**Expected outcome:** Normalization is merged from a separate PR and the config/docs PR contains only configuration and documentation

---

## Step 7: Clean Config/Docs PR

**Objective:** Remove the line-ending normalization commit from the config/docs PR branch

**Details:**

- Drop the normalization commit from `fix-crlf-change-consequences`
- Ensure only config and documentation changes remain
- Keep `.git-blame-ignore-revs` pointing to the normalization commit from the separate PR

**Commands to use:**

```bash
git checkout fix-crlf-change-consequences
git revert 7b57f250
git push
```

**Expected outcome:** Config/docs PR no longer contains any line-ending changes

---

## Step 8: Verify GitLens Works Correctly

**Objective:** Confirm that blame history is restored and changes are no longer visible

**Details:**

- Open any Python file in VS Code
- Use the GitLens blame view (hover over lines or use GitLens sidebar)
- Verify that blame attribution goes back beyond the CRLF commit
- Verify that the CRLF commit is not shown for unrelated line changes
- Test on multiple files to ensure consistency

**How to test:**

1. Open a file modified by the CRLF commit
2. Click on a line to see blame
3. Confirm the blame shows the actual code change author, not the CRLF commit
4. Repeat for 2-3 different files

**Expected outcome:** GitLens shows correct blame history, skipping the CRLF commit

---

## Summary of Changes

| File/Config | Action | Purpose |
|---|---|---|
| `.git-blame-ignore-revs` | Create/Update | List commits that broke blame history |
| `.gitattributes` | Create | Enforce consistent line endings |
| Git config | Update | Set `blame.ignoreRevsFile` |
| Normalization PR | Create | Line ending normalization only |
| Config/docs PR | Clean | No line-ending changes |

---

## Post-Implementation Notes

- Commit these changes: `git add .git-blame-ignore-revs .gitattributes && git commit -m "Configure line ending normalization and blame ignore rules"`
- Push to repository to make changes available to all developers
- Share `.git-blame-ignore-revs` configuration with team
- Document this in project README if helpful for new developers
