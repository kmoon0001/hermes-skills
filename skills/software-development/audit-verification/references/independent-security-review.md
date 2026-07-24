# Independent Security & Concurrency Review

Use this when the task is an **independent review** of a git commit for specification correctness, concurrency safety, resource leaks, error classification, and test coverage — not a PR-review workflow or a claim-verification against a report. Produces a structured verdict.

## Workflow

### 1. Understand the Scope

```bash
# Commit context
git log --oneline -5

# Full diff
git diff HEAD~1..HEAD

# Stat summary (what files, how much changed)
git diff HEAD~1..HEAD --stat
```

Read the diff header/commit message to understand *what* changed and *why*. Group the changes by logical concern (concurrency, I/O, error handling, tests, etc.).

### 2. Diff Review — Each Source Change

For each changed source file:

- **Every `except` clause** — is the exception type right? Is the handler re-raising, swallowing, or converting? Are `BaseException` catches justified (e.g. cleanup-after-acquisition)?
- **Every `finally` block** — does it always run? Could the resource it cleans up have been leaked earlier? Does the `finally` itself raise a new exception that would mask the original?
- **Every resource acquisition** (file open, network call, lock, temp file) — trace the lifecycle to verify the resource is released on **all** exit paths (normal, exception, interruption).
- **Every `raise`** — is the chain correct (`from exc`, `from None`, bare)? Does it preserve or discard evidence?
- **Every `del`** — is the variable actually safe to delete? Unused parameter deletion (`del req, code, msg, headers, newurl`) is unconventional — verify it can't interfere with resource cleanup before the relevant `finally`/`except`.

### 3. Concurrency Safety — Lock Lifecycle Audit

For any lock/mutex/semaphore (`_exclusive_build_lock`, `Lock`, `RLock`, `Semaphore`, OS-level `flock`/`LockFile`):

Build a **path matrix**:

| Exception location | Descriptor/resource leaked? | Lock released on error? |
|---|---|---|
| `os.open` fails (before try) | No — descriptor never assigned | N/A |
| Initialization fails (e.g. write, fsync) | Trace `except BaseException` — is `close()` called before re-raise? | N/A (lock not acquired) |
| Acquisition fails (flock/msvcrt fails) | Same check | N/A (lock not acquired) |
| Normal yield + normal body | `finally` unlocks then closes? | Yes |
| `KeyboardInterrupt` in yield body | Python's `finally` runs — verify unlock + close paths | **Yes — verify** |
| `KeyboardInterrupt` during unlock operation | Python defers signal delivery until `finally` completes | Yes — `close()` in inner `finally` |

Key invariants to assert:
- Every `os.close()` is in a `finally` (or `except BaseException` that re-raises).
- The lock file is **never unlinked** (persistent advisory lock) — verify it's not accidentally deleted.
- Any `import` inside the critical section (e.g. `import msvcrt` / `import fcntl`) is safe — it's a one-time cost and the module is cached after the first import.

### 4. Resource Leak Closure

For **HTTP response bodies / network payloads**:

```python
# Pattern to verify:
except SomeHTTPError as exc:
    try:
        # ... inspect exc.code, decide what to do ...
    finally:
        exc.close()  # MUST be here, not outside
```

Verify every branch inside the inner `try` reaches the `finally`:

| Branch | `exc.close()` reached? |
|---|---|
| Redirect detection (300 ≤ code < 400) | Yes — inner `raise RuntimeError`, then `finally` |
| Permanent error (code ∉ transient set) | Yes — same pattern |
| Transient error (save and retry) | Yes — `last_error = exc`, then `finally` |

For **temp files** (`NamedTemporaryFile` with `delete=False`):

```python
# SAFE pattern — capture path immediately inside the with block
with NamedTemporaryFile(delete=False) as tmp:
    tmp_path = Path(tmp.name)   # ← captured BEFORE write/flush/fsync
    ...

# UNSAFE pattern — capture path AFTER write/flush/fsync
with NamedTemporaryFile(delete=False) as tmp:
    tmp.write(payload)
    tmp.flush()
    os.fsync(tmp.fileno())
    tmp_path = Path(tmp.name)   # ← too late: write error leaks temp file
```

If `write`, `flush`, or `fsync` raises before `tmp_path` is assigned, the `finally` cleanup can't find the file. The leaked `.tmp` file persists on disk. Always capture the path immediately after opening.

### 5. Error Classification Audit

When the code classifies errors (transient vs permanent):

```python
def _is_transient_transport_failure(error: BaseException) -> bool:
    reason = error.reason if isinstance(error, URLError) else error
    if isinstance(reason, TimeoutError):
        return True
    if isinstance(reason, socket.gaierror):
        return reason.errno == socket.EAI_AGAIN
    return isinstance(reason, OSError) and reason.errno in TRANSIENT_ERRNOS
```

Checklist:

- **Missing transient errno** — `EINTR` (interrupted syscall) is often retried internally by Python but not guaranteed on all platforms. `EAGAIN` for non-blocking read/write can be transient but is ambiguous. Note any gaps.
- **Missing transient class** — transient SSL errors (`SSL_ERROR_WANT_READ`, `SSL_ERROR_SYSCALL` wrapping transient errno) could slip through if the errno isn't checked. `ssl.SSLEOFError` with `errno=0` is not retried. Evaluate whether this matters for the target's infrastructure.
- **Over-broad transient** — check that no permanent failures (certificate errors, permanent DNS `EAI_NONAME`, invalid argument `EINVAL`) are incorrectly retried. Verify these are tested.
- **Retry budget** — max attempts × backoff. Is exponential backoff appropriate? Are attempts bounded? Does the last attempt's error propagate as the final exception with the correct chain?

### 6. Test Coverage Audit

For new tests added by the commit:

- **Count them** — `git diff HEAD~1..HEAD -- tests/ | grep "def test_"` for the actual count.
- **Run them** — `python -m pytest ... -x -q` (or equivalent).
- **Verify each test actually tests its claim** — read the test body. Does the assertion match the test name? Are the mock setups correct? Are edge cases exercised?
- **Check parametrized tests** — each parameter set should test a distinct scenario, not just a trivial variation.
- **Look for untested branches** — any `except` clause or conditional path in the new code that lacks a corresponding test? Use coverage reports or manual inspection.

### 7. Produce the Structured Verdict

Use this format:

```markdown
## STRUCTURED VERDICT: APPROVE | APPROVE_WITH_NOTES | REJECT

**Commit:** `<hash>`
**Files:** `<file list>`
**Tests:** `<N/M passed>`

---

### 1. DIFF REVIEW — [No blocking issues | Finding(s) found]

Concise summary of the categories of change. For each finding:

| Severity | Finding | Location |
|---|---|---|
| 🔴 Blocking | <description> | `file.py:NNN` |
| 🟡 Minor | <description> | `file.py:NNN` |
| 🔵 Observation | <description> | `file.py:NNN` |

### 2. CONCURRENCY SAFETY — [No blocking issues | Finding(s) found]

Path matrix outcome (from section 3). Key finding details.

### 3. RESOURCE LEAK CLOSURE — [Confirmed correct | Finding(s) found]

Trace each resource lifecycle. Confirm `finally` always runs.

### 4. TRANSPORT CLASSIFICATION — [No blocking issues | Finding(s) found]

Transient/permanent gaps found (or "none").

### 5. TEST COVERAGE — [All pass and correct | Finding(s) found]

Key tests verified, count confirmed, any missing coverage noted.

### SUMMARY OF FINDINGS

| Severity | Finding | Location |
|---|---|---|
| ... | ... | ... |

**Final verdict: <verdict>** — <one-line rationale>
```

The three verdict levels:
- **APPROVE** — no issues of any severity. Clean ship.
- **APPROVE_WITH_NOTES** — minor issues or observations only. Safe to ship; address findings at maintainer discretion.
- **REJECT** — any blocking issue (🔴). Must be fixed before shipping.
