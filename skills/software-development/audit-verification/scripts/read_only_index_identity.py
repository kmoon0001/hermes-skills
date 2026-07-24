#!/usr/bin/env python3
"""Print a Git index tree ID and staged binary-patch SHA-256 without writing objects."""

from __future__ import annotations

import hashlib
import subprocess


def git(*args: str) -> bytes:
    return subprocess.check_output(["git", *args])


def index_tree_id() -> str:
    object_format = git("rev-parse", "--show-object-format").decode().strip()
    if object_format not in hashlib.algorithms_available:
        raise SystemExit(f"unsupported Git object format: {object_format}")

    root: dict[bytes, object] = {}
    for record in git("ls-files", "--stage", "-z").split(b"\0"):
        if not record:
            continue
        metadata, path = record.split(b"\t", 1)
        mode, oid_hex, stage = metadata.split()
        if stage != b"0":
            raise SystemExit("cannot fingerprint an unmerged index")
        node = root
        parts = path.split(b"/")
        for part in parts[:-1]:
            child = node.setdefault(part, {})
            if not isinstance(child, dict):
                raise SystemExit(f"invalid index path collision at {path!r}")
            node = child
        node[parts[-1]] = (mode, bytes.fromhex(oid_hex.decode("ascii")))

    def hash_tree(node: dict[bytes, object]) -> bytes:
        entries: list[tuple[bytes, bytes]] = []
        for name, value in node.items():
            if isinstance(value, dict):
                mode = b"40000"
                oid = hash_tree(value)
                sort_key = name + b"/"
            else:
                mode, oid = value  # type: ignore[misc]
                sort_key = name
            entries.append((sort_key, mode + b" " + name + b"\0" + oid))
        body = b"".join(entry for _, entry in sorted(entries, key=lambda item: item[0]))
        header = b"tree " + str(len(body)).encode("ascii") + b"\0"
        return hashlib.new(object_format, header + body).digest()

    return hash_tree(root).hex()


def main() -> None:
    # Spell out --full-index even though some Git documentation describes it as
    # implied by --binary. The emitted patch bytes can differ when it is omitted,
    # so explicitness is required for cross-review digest contracts.
    patch = git(
        "diff",
        "--cached",
        "--binary",
        "--full-index",
        "--no-ext-diff",
        "--no-textconv",
    )
    staged_files = git("diff", "--cached", "--name-only", "-z").split(b"\0")
    print(f"index_tree={index_tree_id()}")
    print(f"staged_patch_sha256={hashlib.sha256(patch).hexdigest()}")
    print("staged_files=")
    for path in staged_files:
        if path:
            print(f"  {path.decode('utf-8', errors='surrogateescape')}")


if __name__ == "__main__":
    main()
