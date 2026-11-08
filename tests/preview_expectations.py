"""MVP-1 public development oracle, written from the existing SAS text and
reviewed P2A fixture expectations before preview-generation code or output.
These are review obligations, not observed SAS results or protected gold.
"""

CASE = "sort_and_producer_consumer"
FILE_KEY = "synthetic:main.sas"
SOURCE_SHA256 = "8b29a37635780d63c87111c0856c380334cd6915c749865ef19e61ed058eeaf6"
MODULE = "main"

# Inclusive source lines in the unchanged file. Indices describe source order,
# never independent work units or a permitted schedule.
STEPS = (
    dict(kind="PROC_SORT", lines=(2, 4), reads="work.a", writes="work.sorted"),
    dict(kind="DATA_STEP", lines=(5, 9), reads="work.sorted", writes="work.final"),
)
DEPENDENCY = (0, 1, "DATA", "work.sorted")
SORT_KEYS = ("key", "subkey")
ASSIGNMENT = ("y", "x", "/", "2")

# A proposed acceptance test must distinguish these pairs, without presenting
# hand-computed fixture outputs as measured or independently certified facts.
UNRESOLVED = (
    "Tied rows must not be promised a stable relative order.",
    "Declared composite BY order must not be reduced to key alone.",
    "An ordinary numeric missing key requires explicit ordering checks.",
    "Verify arithmetic on missing x and precision/rounding at representation boundaries.",
    "Check cardinality and preserve original row multiplicities before accepting either candidate.",
    "State continuity across partitions and safe partition boundaries require proof.",
    "No observed execution, speedup, SAS equivalence or parallel eligibility.",
)
STATUS = {
    "artifact_authority": "DRAFT",
    "semantic_verification": "UNVERIFIABLE",
    "semantic_acceptance": "BLOCKED",
    "benchmark_execution": "NOT_RUN",
}
