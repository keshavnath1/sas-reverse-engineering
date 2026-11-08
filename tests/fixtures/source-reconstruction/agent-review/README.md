# INT-5 · Review Copilot notes for the public two-source demo

Use an existing INT-3 package or rebuild it from this copy of the exact INT-4
public inputs. Run from the repository root with the development environment
active, on the existing supported POSIX path. Choose fresh scratch destinations.

```bash
python3.12 -IB scripts/review_intake.py --intake examples/copilot-review/public-input \
  --destination /tmp/sas-re-int1-copilot-demo
```

The expected package manifest SHA-256 is
`8bfc638d5c4db4f60001010ee7abbb3db175c29f44696b0403c621fed953227a`.
Confirm it against the intake command receipt or an independently retained
digest. The record binds the exact manifest bytes, and the validator checks the
manifest-listed report and evidence payloads before resolving citations.

1. Copy `REVIEW_DRAFT.json` to a file outside the evidence package. The draft
   records the observed INT-4 interaction and proposed dispositions.
2. Compare each Copilot claim with the deterministic package. Resolve each
   citation by source path and the exact existing `bytes-START-END` anchor in
   that source's report. Edit each disposition and review note as needed.
   `ACCEPTED`, `REJECTED` and `NEEDS_EVIDENCE` describe the human judgment
   about a claim. A cited span can be relevant to a rejected claim.
3. After reviewing the notes, supply your own reviewer label and change
   `human_approval` from `PENDING` to `APPROVED`. Approval covers the notes,
   including their rejections and open questions. The label and approval are
   operator assertions. The tool checks their presence without authenticating
   the reviewer or adjudicating claim correctness.
4. Save the approved record in a separate fresh directory. Use physical
   paths for `--package` and `--record`. On macOS the receipt uses
   `/private/tmp`. On Linux use `/tmp` for those inputs.

```bash
python3.12 -IB scripts/review_copilot_notes.py \
  --package /private/tmp/sas-re-int1-copilot-demo \
  --record /private/tmp/int5-operator-notes.json \
  --destination /tmp/sas-re-int5-copilot-demo
```

The command writes one deterministic `COPILOT_REVIEW.json` sidecar. Keep it
alongside the package as a separate artifact. Missing approval, invalid
citations or mismatched package bytes cause refusal before output is created.
The manifest digest checks identity against the supplied pin. Retain that pin
independently when provenance matters.

The package remains the source of deterministic TRACE/MAP evidence. The
sidecar separately records Copilot claims and human dispositions. No new
Copilot session is required. Independent behavioral verification remains
unavailable.

```text
artifact_authority: DRAFT
behavioral_evidence: UNAVAILABLE
semantic_verification: UNVERIFIABLE
semantic_acceptance: BLOCKED
reference_experiment: NOT_RUN
benchmark_execution: NOT_RUN
historical_source_run_provenance: UNBOUND
```
