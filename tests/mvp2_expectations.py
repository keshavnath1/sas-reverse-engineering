"""Public source and hand-authored MVP-2 expectations. No application imports.

The relationships below were specified from these bytes before reconstruction
or preview rendering. They are synthetic test obligations, never observed SAS
execution, hidden gold, independently accepted semantics or human approval.
"""

CASE = "ordered_measurements_and_offsets"
SOURCES = {
    "prepare.sas": (
        b"/* PUBLIC SYNTHETIC FIXTURE. Never executed. */\n"
        b"proc sort data=work.observations out=work.ordered;\n"
        b"by batch sequence;\n"
        b"run;\n"
    ),
    "enrich.sas": (
        b"/* PUBLIC SYNTHETIC FIXTURE. Never executed. */\n"
        b"data work.scaled;\n"
        b"set work.ordered;\n"
        b"by batch sequence;\n"
        b"scaled = value / 2;\n"
        b"run;\n"
        b"proc sql;\n"
        b"create table work.adjusted as\n"
        b"select s.batch as batch, s.scaled + r.offset as adjusted\n"
        b"from work.scaled as s inner join work.offsets as r on s.batch = r.batch\n"
        b"where s.scaled > 0\n"
        b"order by batch;\n"
        b"quit;\n"
        b"%include 'postcheck.sas';\n"
    ),
}

# Input rows are declarations only. Duplicate full sort keys in observations,
# duplicate join keys in offsets and missing keys on both sides are deliberate.
INPUTS = (
    ("work.observations", "prepare", ("batch", "sequence", "value"),
     (("2", "1", "8"), ("1", "1", "2"), ("1", "1", "4"), (".", "2", "6"))),
    ("work.offsets", "enrich", ("batch", "offset"),
     (("1", "4"), ("1", "8"), (".", "10"))),
)
SORT_KEYS = ("batch", "sequence")
MISSING_INCLUDE = "postcheck.sas"
MODULES = ("prepare", "enrich")

STEPS = (
    dict(module="prepare", file="prepare.sas", kind="PROC_SORT", lines=(2, 4),
         reads=("work.observations",), writes=("work.ordered",)),
    dict(module="enrich", file="enrich.sas", kind="DATA_STEP", lines=(2, 6),
         reads=("work.ordered",), writes=("work.scaled",)),
    dict(module="enrich", file="enrich.sas", kind="PROC_SQL", lines=(7, 13),
         reads=("work.scaled", "work.offsets"), writes=("work.adjusted",)),
    dict(module="enrich", file="enrich.sas", kind="INCLUDE", lines=(14, 14),
         reads=(), writes=()),
)
# Positions here describe represented source order. They cannot authorize a schedule.
EDGES = (
    (0, 1, "DATA"), (0, 1, "ORDER"), (1, 1, "STATE"), (1, 2, "DATA"),
)
LINEAGE = (
    (0, "work.ordered.value", ("work.observations.value",)),
    (1, "work.scaled.scaled", ("work.ordered.value",)),
    (2, "work.adjusted.batch", ("work.scaled.batch",)),
    (2, "work.adjusted.adjusted", ("work.scaled.scaled", "work.offsets.offset")),
)

# Independent checks on both interpretation and the human-readable package.
# A BY annotation and a STATE self-edge are conservative. The displayed division
# has one current-row operand and a literal; no FIRST/LAST flag, prior-row value,
# RETAIN, SUM or LAG appears in that formula. Partition safety remains unproved.
# SORT takes the two keys in order; tied rows have no promised relative order.
# SQL's ON compares the two batch keys, WHERE tests s.scaled > 0, ORDER BY batch
# alone gives no tie-break. The duplicate-key join may multiply rows; no executed
# row count or physical lookup uniqueness can be asserted.
# The final literal include names absent bytes. Its possible effects on outputs
# remain unknown. No dataset or dependency arrow to a guessed target is valid.
