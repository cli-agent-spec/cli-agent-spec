# REQ-F-070: Atomic Write via Rename

**Tier:** Framework-Automatic | **Priority:** P1

**Source:** Silent assumption — agents assume any file that exists is complete; partial writes from interrupted operations leave corrupt files that look valid

**Addresses:** Severity: High / Token Spend: Low / Time: Low / Context: Low

---

## Description

The framework's file-write utilities MUST use the write-to-tempfile-then-rename pattern for all config files, state files, output files, and lock files. The sequence: write content to a temp file in the same directory as the target (same filesystem, guaranteeing atomic rename), then call `rename(tmpfile, target)`. On POSIX, `rename()` is atomic — readers see either the old complete file or the new complete file, never a partial write.

Framework utilities that write command output to a file (`--output <path>`), persist config, or update state MUST all route through this primitive. Direct `open(target, "w")` writes are prohibited in framework file I/O.

## Acceptance Criteria

- Interrupting a file write mid-operation leaves either the old complete file or no file — never a partially written file
- Two concurrent writes to the same target path do not corrupt the file — one write wins completely
- Temp files are written to the same directory as the target (not `/tmp`), ensuring same-filesystem rename
- Temp files are cleaned up whether the write succeeds or fails
- Works correctly on network filesystems where `rename()` is atomic within a directory

---

## Schema

No dedicated schema type — this requirement governs internal framework I/O utilities

---

## Wire Format

No wire format change — this is an implementation constraint on file write operations

---

## Example

Framework file-write utility (pseudocode):

```python
def atomic_write(target_path, content):
    dir = os.path.dirname(os.path.abspath(target_path))
    fd, tmp_path = tempfile.mkstemp(dir=dir, suffix=".tmp")
    try:
        with os.fdopen(fd, 'w') as f:
            f.write(content)
            f.flush()
            os.fsync(f.fileno())
        os.rename(tmp_path, target_path)   # atomic on POSIX
    except:
        os.unlink(tmp_path)                # clean up on failure
        raise
```

Agent calling `tool config set key=value` during a concurrent `tool config set key=other`:
- One write wins completely — config file is never corrupt
- The losing write's temp file is removed

---

## Related

| Requirement | Tier | Relationship |
|-------------|------|--------------|
| [REQ-F-043](f-043-temp-file-session-scoped-auto-cleanup.md) | F | Extends: temp files created during atomic writes are session-scoped and auto-cleaned |
| [REQ-F-033](f-033-lock-acquisition-with-timeout-and-retry-after-ms.md) | F | Composes: lock files themselves must be written atomically |
| [REQ-F-015](f-015-validate-before-execute-phase-order.md) | F | Composes: file writes occur only in execute phase, after validation |
