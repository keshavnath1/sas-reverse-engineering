"""Build the UNVERIFIED two-module SAS preview in a fresh system scratch directory."""

from pathlib import Path
import sys
from tempfile import TemporaryDirectory

# Isolated Python (-I) omits the script directory. Load only the checkout's
# fixed demo helper, independently of the caller's working directory.
SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))
from mvp1_demo import render_case, run_demo


FIXTURE_GRAPH_SHA256 = "19f41dea50825469a89d8fc545fee1d87f09af946d130d62de8f946d90b78017"


def synthetic_preview(scratch):
    sys.path.insert(0, str(SCRIPTS.parent / "tests"))
    from mvp2_expectations import CASE
    from mvp2_fixture import make_multi_module_case
    from p2a_support import PROFILE_KEY

    with TemporaryDirectory(prefix="sas-re-mvp2-fixture-", dir=scratch) as temporary:
        case = make_multi_module_case(temporary)
        return render_case(case, CASE, FIXTURE_GRAPH_SHA256, PROFILE_KEY,
                           additional_status=("source_consistency", "reconstruction_status", "stage_gate"))


if __name__ == "__main__":
    run_demo("mvp2", __doc__, synthetic_preview)
