"""PY-1: one pure, unverified development candidate, not a SAS interpreter.

Direct calls only; see docs/PY1_VALIDATION.md for the typed public contract.
No source reading, reconstruction, reference-output loading or publication.
"""

from dataclasses import dataclass, field
import math
from typing import Literal


@dataclass(frozen=True, slots=True)
class NumericMissing:
    """Explicit SAS-like missing tag under the development assumption only."""

    tag: str = "."

    def __post_init__(self):
        if (type(self.tag) is not str or not (
            self.tag == "." or len(self.tag) == 2 and self.tag[0] == "."
            and self.tag[1] in "_ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        )):
            raise ValueError("Expected '.', '._', or '.A' through '.Z'")


Numeric = int | float | NumericMissing


@dataclass(frozen=True, slots=True)
class Character:
    """Already stored ASCII text: no padding, truncation or normalization here."""

    text: str

    def __post_init__(self):
        if (type(self.text) is not str or not 1 <= len(self.text) <= 8
                or any(not 32 <= ord(c) <= 126 for c in self.text)):
            raise ValueError("Expected 1-8 stored printable ASCII characters")


@dataclass(frozen=True, slots=True)
class SyntheticRecord:
    case_id: str
    status: Character
    id: Numeric
    numeric_group: tuple[Numeric, ...]       # Public aliases n1 through n12.
    character_group: tuple[Character, ...]  # Public aliases c1 through c5.
    initial_default: Numeric = field(default_factory=NumericMissing)


@dataclass(frozen=True, slots=True)
class CandidateOutput:
    case_id: str
    id: Numeric
    numeric_group: tuple[Numeric, ...]
    character_group: tuple[Character, ...]
    default: Numeric


@dataclass(frozen=True, slots=True)
class TraceEvent:
    rule_index: int
    action: str
    predicate_result: bool | None
    source_lines: tuple[int, int]  # Inclusive original TRACE coordinates.
    source_bytes: tuple[int, int]  # Half-open original TRACE coordinates.


@dataclass(frozen=True, slots=True)
class CandidateResult:
    mode: Literal["full", "isolated_pair"]
    disposition: Literal["SURVIVED", "EXCLUDED"]
    output: CandidateOutput | None
    first_exclusion_rule: int | None
    label_assignment_branch: int | None
    trace: tuple[TraceEvent, ...]
    artifact_authority: str = field(default="DRAFT", init=False)
    behavioral_evidence: str = field(default="UNAVAILABLE", init=False)
    semantic_verification: str = field(default="UNVERIFIABLE", init=False)
    semantic_acceptance: str = field(default="BLOCKED", init=False)
    reference_experiment: str = field(default="NOT_RUN", init=False)
    benchmark_execution: str = field(default="NOT_RUN", init=False)


# Navigation references to existing TRACE records, not new evidence identities.
# No source text, private status literals, filename or content digest is embedded.
# These coordinates are not runtime verification of any supplied source version.
_SOURCE_SPANS = (
    ((317, 317), (13097, 13161)),
    ((319, 319), (13167, 13215)),
    ((320, 320), (13220, 13272)),
    ((322, 322), (13278, 13305)),
    ((324, 326), (13311, 13495)),
    ((328, 329), (13501, 13604)),
)


def _validate_numeric(value):
    if type(value) is NumericMissing:
        return
    if type(value) is int and -(2**53) <= value <= 2**53:
        return
    if type(value) is float and math.isfinite(value):
        return
    raise ValueError("Expected a finite float, exact-range int, or NumericMissing")


def _validate_record(row):
    # Validate the entire contract before business execution, including fields
    # whose rules might not be reached. Invalid inputs are not excluded rows.
    if type(row) is not SyntheticRecord:
        raise ValueError("Expected one SyntheticRecord")
    if (type(row.case_id) is not str or len(row.case_id) != 3
            or not row.case_id.isascii() or not row.case_id.isalnum()):
        raise ValueError("case_id must be three ASCII letters/digits")
    if type(row.status) is not Character or len(row.status.text) != 8:
        raise ValueError("status must be a stored Character of width 8")
    if type(row.numeric_group) is not tuple or len(row.numeric_group) != 12:
        raise ValueError("numeric_group must be the ordered 12-element tuple")
    if type(row.character_group) is not tuple or len(row.character_group) != 5:
        raise ValueError("character_group must be the ordered 5-element tuple")
    for value in (row.id, row.initial_default, *row.numeric_group):
        _validate_numeric(value)
    if any(type(value) is not Character or len(value.text) != 4
           for value in row.character_group):
        raise ValueError("character_group values must be stored Characters of width 4")


def prepare(row: SyntheticRecord, *, mode: Literal["full", "isolated_pair"] = "full") -> CandidateResult:
    """Evaluate one typed public row under explicitly unverified assumptions.

    ValueError refuses unsupported forms before evaluation. 'isolated_pair'
    omits rule 0 only; it does not demonstrate full-sequence fallthrough.
    Diagnostics describe this Python call, never an observed SAS execution.
    """
    if type(mode) is not str or mode not in ("full", "isolated_pair"):
        raise ValueError("mode must be 'full' or 'isolated_pair'")
    _validate_record(row)
    trace = []
    label_branch = None
    default = row.initial_default

    def emit(rule, action, result=None):
        trace.append(TraceEvent(rule, action, result, *_SOURCE_SPANS[rule]))

    def finish(exclusion=None):
        if exclusion is not None:
            emit(exclusion, "EXCLUDE_CURRENT_ROW")
            output = None
        else:
            output = CandidateOutput(row.case_id, row.id, row.numeric_group,
                                     row.character_group, default)
        return CandidateResult(mode, "EXCLUDED" if exclusion is not None else "SURVIVED",
                               output, exclusion, label_branch, tuple(trace))

    # Public aliases, compared as already-stored fixed-width ASCII values.
    if mode == "full":
        excluded = row.status.text not in ("A       ", "B       ")
        emit(0, "PREDICATE", excluded)
        if excluded:
            return finish(0)

    first = row.status.text == "A       "
    emit(1, "PREDICATE", first)
    if first:
        default = 1
        label_branch = 1
        emit(1, "ASSIGN_DEFAULT_1")
    else:
        alternative = row.status.text == "B       "
        emit(2, "PREDICATE", alternative)
        if alternative:
            default = 0
            label_branch = 2
            emit(2, "ASSIGN_DEFAULT_0")
        else:
            emit(2, "NO_ASSIGNMENT_BY_PAIR")

    # Rejoin is outside both branches. Rule 3 needs only rule 0 false in full
    # mode; rule 4 additionally needs 3 false; rule 5 needs 3 and 4 false.
    excluded = type(row.id) is NumericMissing
    emit(3, "PREDICATE", excluded)
    if excluded:
        return finish(3)

    # Count every argument in original tuple order. This deliberately makes no
    # claim about SAS CMISS laziness or internal argument evaluation strategy.
    excluded = sum(type(value) is NumericMissing for value in row.numeric_group) > 0
    emit(4, "PREDICATE", excluded)
    if excluded:
        return finish(4)

    excluded = sum(value.text == "    " for value in row.character_group) > 0
    emit(5, "PREDICATE", excluded)
    if excluded:
        return finish(5)
    return finish()
