"""Frozen public specification for the MVP-2 SORT → DATA → SQL example.

Numeric cells are strings. Inputs admitted by these vectors are small signed
integers or "." (ordinary numeric missing). Nonmissing results are exact for
the selected integers and halves. Do not treat ".", zero and NaN as equivalent.
Ordinary missing sorts before finite numbers, equals another ordinary missing
batch in this local PROC SQL equijoin, and propagates through / and +. A scaled
value that is missing, zero or negative fails WHERE scaled > 0.

Stages use (batch, sequence, value), (batch, sequence, value, scaled), and
(batch, adjusted), respectively. The expected rows below show ONE legal order.
Check ascending composite keys at SORT, allowing any order within full-key
ties. DATA retains the chosen SORT row order and its original three fields.
The assignment uses only the current value. An INNER JOIN emits each qualifying
pair of equal batches; repeated identical projected rows count separately.
Final batches ascend; compare the multiset of projected rows in each batch.
The input sequence is absent from that final projection and its ordering rule.

O4, %include 'postcheck.sas', is unresolved. Every full-workflow gate stays
BLOCKED; do not attach modeled outputs to O4. These development expectations
are hand computations from the original source, not observations of SAS.
"""

# Original public declarations from mvp2_expectations.INPUTS. The tests check
# these copies against the originals. This data file imports no implementation.
FIXTURES = {
    "mvp2": {
        "observations": (("2", "1", "8"), ("1", "1", "2"),
                         ("1", "1", "4"), (".", "2", "6")),
        "offsets": (("1", "4"), ("1", "8"), (".", "10")),
        "split_after": 2,  # cut between the two (1, 1) rows in sorted input
        "expected": {
            "ordered": ((".", "2", "6"), ("1", "1", "2"),
                        ("1", "1", "4"), ("2", "1", "8")),
            "scaled": ((".", "2", "6", "3"), ("1", "1", "2", "1"),
                       ("1", "1", "4", "2"), ("2", "1", "8", "4")),
            "adjusted": ((".", "13"), ("1", "5"), ("1", "9"),
                         ("1", "6"), ("1", "10")),
        },
    },
    "filters": {
        "observations": (("2", "0", "6"), ("1", "2", "3"),
                         ("1", "0", "."), ("1", "-1", "-2"), ("1", ".", "0")),
        "offsets": (("1", "2"), ("1", "2"), ("1", "."), ("9", "4")),
        "expected": {
            "ordered": (("1", ".", "0"), ("1", "-1", "-2"), ("1", "0", "."),
                        ("1", "2", "3"), ("2", "0", "6")),
            "scaled": (("1", ".", "0", "0"), ("1", "-1", "-2", "-1"),
                       ("1", "0", ".", "."), ("1", "2", "3", "1.5"),
                       ("2", "0", "6", "3")),
            # Only 1.5 qualifies AND matches. Both identical 2s and the
            # missing offset participate. No opposite-side match for 2 or 9.
            "adjusted": (("1", "3.5"), ("1", "3.5"), ("1", ".")),
        },
    },
    "sequence_witness": {
        "observations": (("1", "2", "8"), ("2", "1", "6"), ("1", "1", "2")),
        "offsets": (("1", "1"), ("2", "2")),
        "expected": {
            "ordered": (("1", "1", "2"), ("1", "2", "8"), ("2", "1", "6")),
            "scaled": (("1", "1", "2", "1"), ("1", "2", "8", "4"),
                       ("2", "1", "6", "3")),
            "adjusted": (("1", "2"), ("1", "5"), ("2", "5")),
        },
    },
    "special_missing": {
        "observations": ((".A", "1", "4"),), "offsets": ((".A", "1"),),
        "expected": None,  # unqualified special-missing profile
    },
    "precision": {
        "observations": (("1", "1", "9007199254740993"),), "offsets": (("1", "1"),),
        "expected": None,  # casting to float may collapse 2**53+1 into 2**53
    },
}

# A second valid SQL projection for sequence_witness. The row producing 5
# has sequence 2; the one producing 2 has sequence 1. The projected columns
# themselves carry no sequence. Rejecting this permutation is the policy bug;
# merely PRODUCING a different legal tie permutation is never that bug.
FINAL_TIE_WITNESS = (("1", "5"), ("1", "2"), ("2", "5"))

# (input fixture, fixed demonstration probe, modeled verdict, first violation).
# baseline on precision/special_missing has no approved expected observations.
CASES = {
    "B01-published-workflow": ("mvp2", "baseline", "PASS", None),
    "B02-filter-and-fanout": ("filters", "baseline", "PASS", None),
    "B03-sequence-coincidence": ("sequence_witness", "baseline", "PASS", None),
    "B04-split-by-group": ("mvp2", "split", "PASS", None),
    "B05-upstream-tie-permutation": ("mvp2", "reverse_sort_ties", "PASS", None),
    "B06-final-tie-permutation": ("sequence_witness", "reverse_final_ties", "PASS", None),
    "B07-wrong-sort-order": ("mvp2", "wrong_sort", "FAIL", "ordered"),
    "B08-wrong-final-order": ("sequence_witness", "wrong_final_order", "FAIL", "adjusted"),
    "B09-lost-duplicate-match": ("filters", "drop_matches", "FAIL", "adjusted"),
    "B10-wrong-arithmetic": ("mvp2", "wrong_scale", "FAIL", "scaled"),
    "B11-detached-data-ties": ("mvp2", "decouple_ties", "FAIL", "scaled"),
    "B12-overstrict-sequence": ("sequence_witness", "strict_sequence", "FAIL", "final_order_policy"),
    "B13-unfiltered-join": ("filters", "skip_where", "FAIL", "adjusted"),
    "B14-missing-key-mismatch": ("mvp2", "ignore_missing_key", "FAIL", "adjusted"),
    "B15-special-missing": ("special_missing", "baseline", "UNVERIFIABLE", None),
    "B16-precision-boundary": ("precision", "baseline", "UNVERIFIABLE", None),
    # PASS refers to O1–O3 only. O4 is always UNVERIFIABLE and blocks the workflow.
    "B17-unresolved-include": ("mvp2", "unresolved_include", "PASS", None),
}
