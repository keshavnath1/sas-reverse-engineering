#!/usr/bin/env python3
"""Input file hashes only: no SAS parsing, AI calls or approval semantics."""
import argparse
import hashlib
import json
from pathlib import Path


def digest(path):
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def snapshot(input_root):
    root = Path(input_root)
    if root.is_symlink() or not root.is_dir():
        raise ValueError("Input must be an existing nonsymlink directory")
    files = []
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise ValueError("Symlinks are not allowed: " + path.relative_to(root).as_posix())
        if path.is_dir():
            continue
        if not path.is_file():
            raise ValueError("Input contains a nonregular file")
        files.append({"path": path.relative_to(root).as_posix(),
                      "size": path.stat().st_size, "sha256": digest(path)})
    if not files:
        raise ValueError("Input has no files")
    body = {"version": 1, "files": files}
    canonical = json.dumps(body, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return {**body, "snapshot_sha256": hashlib.sha256(canonical).hexdigest()}


def outside_input(input_root, manifest):
    target = Path(manifest)
    if target.is_symlink():
        raise ValueError("Manifest must not be a symlink")
    try:
        target.resolve().relative_to(Path(input_root).resolve())
    except ValueError:
        return target
    raise ValueError("Manifest must be outside the read-only input directory")


def create(input_root, manifest):
    target = outside_input(input_root, manifest)
    record = snapshot(input_root)
    # Exclusive creation: never overwrite an existing snapshot.
    with target.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(record, indent=2, ensure_ascii=True) + "\n")
    return record["snapshot_sha256"]


def unique_object(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise ValueError("Duplicate manifest key")
        value[key] = item
    return value


def check(input_root, manifest):
    target = outside_input(input_root, manifest)
    expected = json.loads(target.read_text(encoding="utf-8"), object_pairs_hook=unique_object)
    actual = snapshot(input_root)
    if expected != actual:
        raise ValueError("Input changed or snapshot is invalid; preserve this run and start a new one")
    return actual["snapshot_sha256"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("create", "check"))
    parser.add_argument("--input", required=True)
    parser.add_argument("--manifest", required=True)
    args = parser.parse_args()
    try:
        result = (create if args.mode == "create" else check)(args.input, args.manifest)
    except (OSError, ValueError) as error:
        parser.exit(1, "SNAPSHOT FAILED: " + str(error) + "\n")
    print("SNAPSHOT " + args.mode.upper() + ": " + result)


if __name__ == "__main__":
    main()
