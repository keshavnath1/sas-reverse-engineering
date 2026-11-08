"""Print the decision review for the fixed, public MVP-2 subject and complete MVP-3 report."""

import argparse
from hashlib import sha256
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory

from sas_re._decision_review import ReviewBindingError, render_review
from sas_re._io_common import EvidenceError
from sas_re.platform_io import require_evidence_io
from sas_re.semantic import validate_v2


ROOT = Path(__file__).resolve().parents[1]
# Bind the local review's reference and ADR links to the accepted documents.
REFERENCES = {
    "examples/mvp2/EVIDENCE.md": "2e12f17fea8a55d5f8bf6f5e108a68575af82c5891cc70a8db349aa61d432ff7",
    "examples/mvp2/ADR_NATIVE.md": "dd0f1211dfc98599f7316a3a8aeae08308b54453cc5de8025cd3837fc8dc36a7",
    "examples/mvp2/ADR_SPARK.md": "531cb320a8e681b315470819ddeeedecf7439e6fcdefb9d4a1735aa2f3fed80c",
    "docs/MVP3_VALIDATION.md": "d14e589f12ef8f5689f4f314ba8055542e88b68db52bccd527eb930a442e228d",
}


def verify_references():
    for name, expected in REFERENCES.items():
        if sha256((ROOT / name).read_bytes()).hexdigest() != expected:
            raise ReviewBindingError("REFERENCED_DOCUMENT_MISMATCH")


def fixed_review():
    require_evidence_io()
    verify_references()
    sys.path[:0] = [str(ROOT / "scripts"), str(ROOT / "tests")]
    try:
        from mvp3_tieout import build_report

        # Verify the source declarations and case table as literal data before
        # the reconstruction fixture imports those source declarations.
        report_bytes = (json.dumps(build_report(), allow_nan=False) + "\n").encode("utf-8")
        from mvp1_demo import scratch_destination
        from mvp2_fixture import make_multi_module_case
        from p2a_support import PROFILE_KEY
    finally:
        del sys.path[:2]

    scratch, _ = scratch_destination("/tmp/sas-re-mvp4-fixture", "mvp4")
    with TemporaryDirectory(prefix="sas-re-mvp4-fixture-", dir=scratch) as temporary:
        scope, inventory, profile, graph = make_multi_module_case(temporary)
        status = validate_v2(scope, inventory, graph, profile, profile_file_key=PROFILE_KEY)
        if (status["source_consistency"], status["reconstruction_status"], status["stage_gate"]) != (
                "PASSED", "PARTIAL", "BLOCKED"):
            raise ReviewBindingError("MVP2_RECONSTRUCTION_MISMATCH")
        return render_review(graph, report_bytes)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    try:
        review = fixed_review()
    except (EvidenceError, RuntimeError, OSError) as err:
        parser.exit(2, f"BLOCKED: {err}\n")
    sys.stdout.buffer.write(review)


if __name__ == "__main__":
    main()
