"""Build the UNVERIFIED public SORT/DATA preview in a fresh system scratch directory."""

import argparse
from contextlib import suppress
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys
from tempfile import TemporaryDirectory

from sas_re._dependency_diagnostics import diagnose
from sas_re._draft_preview import generate_preview
from sas_re.platform_io import require_evidence_io
from sas_re.safeio import EvidenceError, require_safe_root
from sas_re.semantic import validate_v2


FIXTURE = "sort_and_producer_consumer"
# Exact historical reconstruction already recorded in docs/P3_A1_VALIDATION.md.
FIXTURE_GRAPH_SHA256 = "385423530208b08635de832bed57698b7278490f2cb7a43f08fd754b80df9155"
FILES = ("ADR_NATIVE.md", "ADR_SPARK.md", "ARCHITECTURE.md", "EVIDENCE.md", "MODULES.md", "PRD.md")


def scratch_destination(argument):
    # Only a new direct child of system scratch. Never descend through a
    # caller-selected tree: an evidence store or sealed attempt can have any name.
    parent, leaf = os.path.split(argument)
    scratch = Path("/private/tmp" if sys.platform == "darwin" else "/tmp")
    if parent not in {"/tmp", str(scratch)} or not re.fullmatch(r"sas-re-mvp1-[A-Za-z0-9_-]{1,64}", leaf):
        raise ValueError("choose a new /tmp/sas-re-mvp1-<label> directory")
    require_safe_root(scratch)
    info = scratch.stat()
    if info.st_uid != 0 or not info.st_mode & stat.S_ISVTX:
        raise ValueError("system scratch must be a root-owned sticky directory")
    return scratch, leaf


def synthetic_preview(scratch):
    # Development-only: the fixture and its adapter live in the checkout.
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tests"))
    from p2a_expectations import PUBLIC_CASES
    from p2a_support import PROFILE_KEY, make_case

    with TemporaryDirectory(prefix="sas-re-mvp1-fixture-", dir=scratch) as temporary:
        scope, inventory, profile, graph = make_case(temporary, PUBLIC_CASES[FIXTURE], attempt="reconstruct-1")
        report = validate_v2(scope, inventory, graph, profile, profile_file_key=PROFILE_KEY)
        diagnostics = diagnose(graph, FIXTURE_GRAPH_SHA256)
        files = generate_preview(graph, diagnostics)
    return files, {"status": "UNVERIFIED", "fixture": FIXTURE, "graph_sha256": diagnostics["parent_graph_sha256"],
                   **{field: report[field] for field in ("artifact_authority", "semantic_verification",
                                                         "semantic_acceptance", "benchmark_execution")}}


def write_bundle(scratch, leaf, files):
    if set(files) != set(FILES):
        raise ValueError("unexpected preview file manifest")
    destination = scratch / leaf
    destination.mkdir(mode=0o700)  # Exclusive, including when an existing name is a symlink.
    try:
        directory = os.open(destination, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    except BaseException:
        with suppress(OSError):
            destination.rmdir()
        raise
    created = []
    try:
        for name in FILES:
            fd = os.open(name, os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW, 0o600, dir_fd=directory)
            created.append(name)
            with os.fdopen(fd, "wb") as output:
                output.write(files[name])
    except BaseException:
        for name in created:
            with suppress(OSError):
                os.unlink(name, dir_fd=directory)
        with suppress(OSError):
            destination.rmdir()
        raise
    finally:
        os.close(directory)
    return [{"name": name, "bytes": len(files[name]), "sha256": hashlib.sha256(files[name]).hexdigest()}
            for name in FILES]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--destination", required=True, help="new /tmp/sas-re-mvp1-<label> directory")
    args = parser.parse_args()
    try:
        require_evidence_io()  # Deny unsupported platforms before any fixture or destination I/O.
        scratch, leaf = scratch_destination(args.destination)
        files, manifest = synthetic_preview(scratch)
        manifest["files"] = write_bundle(scratch, leaf, files)
    except EvidenceError as error:
        parser.exit(2, f"{error.gate}: {error.code}\n")
    except FileExistsError:
        parser.exit(2, "destination already exists; choose a new directory\n")
    except (OSError, ValueError) as error:
        parser.exit(2, f"preview failed: {error}\n")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
