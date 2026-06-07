# Release Checklist

This workspace was not a Git repository during release preparation, so tagging and publishing could not be executed directly here.

## 1. Commit

```bash
git init
git add .
git commit -m "Release v1.0.0 - competition submission"
```

If the repository is already connected to Git, omit `git init`.

## 2. Create Tag

```bash
git tag -a v1.0.0 -m "pharos-dtvm-bridge v1.0.0"
```

## 3. Push Main and Tag

```bash
git push origin main
git push origin v1.0.0
```

If the default branch is not `main`, replace `main` with the active release branch.

## 4. Create GitHub Release

Release title:

```text
v1.0.0 — Competition Submission Release
```

Release description:

Use the contents of `RELEASE_NOTES_v1.0.0.md`.

## 5. Pre-Publish Validation

Run:

```bash
python demo/run_demo.py
python bin/pharos-dtvm-bridge.py "Write ERC20 in Rust and call from Solidity"
python -m compileall cli.py engine demo bin
```

Expected:

- demo prints success and ABI mismatch sections
- branded CLI prints logs and JSON
- compile check completes without syntax errors
