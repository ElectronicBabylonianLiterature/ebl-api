# ✅ CRLF Line Ending Fix - Team Instructions

## Overview

A recent PR (#671 - Backend optimization) inadvertently changed line endings across 600+ files, which caused GitLens blame history to become unusable. This fix addresses that issue and prevents it from happening again.

---

## 🎯 What Changed

| Issue | Solution |
|-------|----------|
| GitLens showed all lines pointing to CRLF commit | Created `.git-blame-ignore-revs` to exclude whitespace-only commits |
| 600+ files still had inconsistent line endings | Created normalization commit (1213c20e) in a separate PR to enforce LF globally |
| Git blame not configured | Set `blame.ignoreRevsFile` in git config |
| Future CRLF disasters possible | Added `.gitattributes` with LF enforcement rules |

---

## 📥 What You Need to Do

### Step 1: Pull the Latest Changes

```bash
git pull origin master
# or if you're on a feature branch:
git fetch origin
git merge origin/master
```

### Step 2: Update Git Configuration (Local)

After pulling, run this command **once per repository**:

```bash
git config blame.ignoreRevsFile .git-blame-ignore-revs
```

✅ **That's it!** Git blame will now automatically ignore whitespace-only commits.

### Step 3: (Optional) Update VS Code Settings

For enhanced GitLens support, add this to your workspace `.vscode/settings.json`:

```json
{
  "gitlens.advanced.blameIgnoreRevsFile": ".git-blame-ignore-revs",
  "gitlens.blame.ignoreWhitespace": true
}
```

If you don't have a `.vscode/settings.json` file, create one in the project root.

---

## ✨ What Improves Now

✅ **GitLens Blame History** — Shows correct authors for code, not CRLF commits  
✅ **Git Blame Output** — `git blame <file>` now respects ignore rules  
✅ **Clean History** — Whitespace-only commits are hidden from blame  
✅ **Future Safety** — `.gitattributes` prevents line-ending disasters  

---

## 🔍 How to Verify It Works

### Test Git Blame (Command Line)

```bash
# Should NOT show 2fc6fea0 (original CRLF commit) for real code:
git blame ebl/app.py | head -20

# Should NOT show 1213c20e (normalization commit) for code content:
git blame ebl/errors.py | grep "^[^1]"
```

### Test in GitLens (VS Code)

1. Open any Python file
2. Hover over a line of code
3. Check the blame annotation — should show original author, not CRLF commits
4. Lines with only whitespace changes may briefly show 1213c20e before being ignored

### Expected Output

```
✅ CORRECT:
3317e80aa (Jussi Laasonen 2018-11-21) class NotFoundError(Exception):
1d0837eb2 (Jussi Laasonen 2019-01-23) class DuplicateError(Exception):

❌ WRONG (before fix):
2fc6fea0 (Some Author    2026-02-05) class NotFoundError(Exception):
```

---

## 📚 Files to Know About

| File | Purpose | Needs Tracking? |
|------|---------|-----------------|
| `.git-blame-ignore-revs` | List of commits to ignore in blame | ✅ YES (committed) |
| `.gitattributes` | Enforce LF line endings globally | ✅ YES (committed) |
| `.git/config` | Git configuration (your local machine) | ❌ NO (local only) |
| `.vscode/settings.json` | VS Code workspace settings | ❌ NO (in .gitignore) |

---

## ⚠️ Important Notes

1. **Git version requirement**: You need Git 2.23+ (most developers have this)

   ```bash
   git --version  # Should be 2.23.0 or newer
   ```

2. **The `.git/config` change is local**: Each developer needs to run the config command once. It won't auto-sync.

3. **`.vscode/settings.json` is optional but recommended**: It's in `.gitignore` because different teams may have different preferences.

4. **No code changes**: This PR only fixes the blame history issue — no functional code changes.

---

## 🆘 Troubleshooting

### "GitLens still shows the CRLF commit"

- [ ] Did you run `git config blame.ignoreRevsFile .git-blame-ignore-revs`?
- [ ] Did you reload VS Code?
- [ ] Check: `git config blame.ignoreRevsFile` (should output `.git-blame-ignore-revs`)

### "I see 1213c20e on many lines"

This is normal for whitespace-only changes. It means:

- The line had CRLF/LF inconsistency
- Our normalization commit (1213c20e) fixed it
- Git blame is correctly showing this

The ignore rules will hide these from blame once GitLens reloads.

### "Old CRLF commit (2fc6fea0) still shows up"

- This is expected only for lines that had actual code changes in that commit
- Check if the line is really code or just whitespace
- Reload VS Code and GitLens

---

## 📖 Additional Resources

- **Why this happened**: [GitHub discussion on CRLF issues](https://github.com/ElectronicBabylonianLiterature/ebl-api/discussions)
- **Git blame ignore documentation**: `git help blame` → search for `ignoreRevsFile`
- **Project setup guide**: See `README.md` for full development environment setup

---

## Questions?

If you have issues or questions:

1. Check the troubleshooting section above
2. Verify your git version (`git --version`)
3. Confirm config is set: `git config blame.ignoreRevsFile`
4. Ask in the team channel or create an issue

**Thank you for your patience while we fixed this!**
