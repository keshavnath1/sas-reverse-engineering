---
name: sas-reconstruct
description: Reconstruct or trace the fixed public synthetic SAS workflow with the existing offline Python engine. Use for source identity, module ownership, data flow, dependency edges, and unresolved evidence.
---

Use the [public review package](../../examples/offline-review/README.md) for inspection. For a requested fresh reconstruction, run from this checkout with the prepared Python 3.12 environment active on a supported POSIX development host. Choose an unused destination; preserve any existing directory.

```bash
python3.12 -IB scripts/review_workflow.py --destination /tmp/sas-re-review-sk1
```

The [entry script](../../scripts/review_workflow.py) owns the inputs. P1 inventories original bytes and hashes. P2A reconstructs one canonical v2 graph and checks its source consistency. This fixture exercises PROC SORT, DATA/SET with composite BY keys and a current-row assignment, a bounded PROC SQL equijoin with WHERE and ORDER BY, and a literal unresolved include. Use the [P2A subset](../../docs/P2A_DESIGN.md#closed-source-profile) to distinguish supported forms from unknown effects. P3-A1's [diagnostics](../../src/sas_re/_dependency_diagnostics.py) check the supplied graph and identify represented paths, cycles, conflicts and missing proof. Leave parsing, hashing and diagnostics to Python.

1. Open the README named by the successful receipt. Read [MANIFEST.json](../../examples/offline-review/MANIFEST.json) from that same package. Check the subject `ordered_measurements_and_offsets`, graph SHA-256 `19f41dea50825469a89d8fc545fee1d87f09af946d130d62de8f946d90b78017`, payload names and digests. A live run gives you a separate manifest digest in stdout. Identify a checked-in sample explicitly if that is what you inspected.
2. Trace the requested boundary in [EVIDENCE.md](../../examples/offline-review/EVIDENCE.md). For example, follow the E4 DATA and E2 ORDER records for `work.ordered` from O1 in `prepare` to O2 in `enrich`. Preserve the canonical IDs behind those local labels, the fact index, source file, line numbers and half-open byte span. A missing path leaves independence unproved.
3. Return a short trace with the subject, producing and consuming modules, cited transformations, unresolved effects and the stage gate. Hand the evidence references to requirements review without editing the generated files.

Stop on a refused command, mismatched digest or missing evidence. O4 names `postcheck.sas` without authorized target bytes: report PARTIAL reconstruction and a BLOCKED full-workflow gate. Keep unsupported syntax unresolved. Never search for an include, accept private paths or execute SAS to fill a gap. Native Windows evidence I/O remains BLOCKED. The [downstream pin](../../docs/COMPATIBILITY.md) is read-only.

```text
artifact_authority: DRAFT
semantic_verification: UNVERIFIABLE
semantic_acceptance: BLOCKED
benchmark_execution: NOT_RUN
```
