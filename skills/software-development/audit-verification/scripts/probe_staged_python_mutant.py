#!/usr/bin/env python3
"""Prove that one staged Python test kills one narrowly defined staged-source mutant.

The repository is never edited. The script first runs the requested test against the
ordinary worktree (which must match the index for both source and test), then loads a
single textual mutation of the exact staged source blob into ``sys.modules`` and reruns
the test. Exit codes: 0 mutant killed, 1 mutant survived, 2 precondition/infrastructure
failure.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import types


def _run(command: list[str], *, capture: bool = False) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return subprocess.run(
        command,
        check=False,
        capture_output=capture,
        text=True,
        env=env,
    )


def _emit(*, status: str, detail: str, exit_code: int) -> int:
    print(json.dumps({"status": status, "detail": detail}, sort_keys=True))
    return exit_code


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--module", required=True, help="Import name, e.g. pkg.module")
    parser.add_argument("--source-path", required=True, help="Repository-relative .py path")
    parser.add_argument("--test-node", required=True, help="Exact pytest node id")
    parser.add_argument("--old", required=True, help="Unique staged-source text to replace")
    parser.add_argument("--new", required=True, help="Replacement text for the mutant")
    parser.add_argument("--expected-count", type=int, default=1)
    args = parser.parse_args()

    sys.dont_write_bytecode = True
    source_path = Path(args.source_path).as_posix()
    test_path = args.test_node.split("::", 1)[0]

    if args.expected_count < 1:
        return _emit(
            status="error",
            detail="expected-count must be positive",
            exit_code=2,
        )

    # A worktree-based pytest collection is valid only when both files match the index.
    clean = _run(
        ["git", "diff", "--quiet", "--", source_path, test_path],
        capture=True,
    )
    if clean.returncode != 0:
        return _emit(
            status="error",
            detail="source or test has unstaged changes; staged/worktree snapshot is split",
            exit_code=2,
        )

    blob = _run(["git", "show", f":{source_path}"], capture=True)
    if blob.returncode != 0:
        diagnostic = blob.stderr.strip() or "git show failed"
        return _emit(status="error", detail=diagnostic, exit_code=2)

    actual_count = blob.stdout.count(args.old)
    if actual_count != args.expected_count:
        return _emit(
            status="error",
            detail=(
                f"mutation anchor count was {actual_count}, expected {args.expected_count}"
            ),
            exit_code=2,
        )

    baseline = _run(
        [
            sys.executable,
            "-B",
            "-m",
            "pytest",
            "-p",
            "no:cacheprovider",
            args.test_node,
            "-q",
        ]
    )
    if baseline.returncode != 0:
        return _emit(
            status="error",
            detail=f"baseline test failed with pytest exit {baseline.returncode}",
            exit_code=2,
        )

    package = args.module.rpartition(".")[0]
    if package:
        importlib.import_module(package)

    module = types.ModuleType(args.module)
    module.__file__ = source_path
    module.__package__ = package
    module.__spec__ = importlib.util.spec_from_loader(args.module, loader=None)
    sys.modules[args.module] = module

    mutated_source = blob.stdout.replace(args.old, args.new)
    try:
        exec(compile(mutated_source, source_path, "exec"), module.__dict__)
    except Exception as exc:
        return _emit(
            status="error",
            detail=f"mutant did not compile/load: {type(exc).__name__}: {exc}",
            exit_code=2,
        )

    try:
        import pytest
    except Exception as exc:
        return _emit(
            status="error",
            detail=f"pytest import failed: {type(exc).__name__}: {exc}",
            exit_code=2,
        )

    mutant_rc = int(
        pytest.main(["-p", "no:cacheprovider", args.test_node, "-q"])
    )
    if mutant_rc == 1:
        return _emit(
            status="killed",
            detail="targeted test failed under the in-memory staged-source mutant",
            exit_code=0,
        )
    if mutant_rc == 0:
        return _emit(
            status="survived",
            detail="targeted test still passed under the in-memory staged-source mutant",
            exit_code=1,
        )
    return _emit(
        status="error",
        detail=f"mutant pytest run ended with non-semantic exit {mutant_rc}",
        exit_code=2,
    )


if __name__ == "__main__":
    raise SystemExit(main())
