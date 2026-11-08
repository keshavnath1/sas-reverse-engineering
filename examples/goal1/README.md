# GOAL-1 public modernization review

Start with [TRACE and MAP](TRACE_MAP.md), then review the [draft PRD and module specifications](REQUIREMENTS.md), [dependency and optimization assessment](OPTIMIZATION.md), [HLD, LLD and draft ADRs](ARCHITECTURE.md), and [validation and implementation inventory](VALIDATION.md). The [manifest](MANIFEST.json) binds this review's files, the existing public INTG-3 subject and the retained engineering outputs by SHA-256 and byte count. Each engineering manifest in turn binds its own payload. The bound evidence stays in its existing packages.

This is an AI-authored draft over deterministic source evidence and candidate output. No GOAL-1 Copilot session or human review was performed. INTG-4 remains **FAIL**. INTG-4R remains **PASS** for the human-corrected public engineering continuation. Its approvals apply to its exact claim records and subjects. GOAL-1 requires its own human review.

## Resolve the evidence

From the checkout root with the Python 3.12 development installation, run these commands using fresh scratch destinations.

```sh
python3.12 -IB scripts/review_mig5.py prepare --scenario passes --destination /tmp/goal1-passes
python3.12 -IB scripts/review_mig5.py prepare --scenario duplicates --destination /tmp/goal1-duplicates
```

Compare the generated manifests and the files they list with `review_subjects` in the GOAL-1 manifest. Its `engineering_runs` entries identify the retained INTG-4R publications. To reproduce those exact publications, use the original claim and approval bytes with the [INTG-3 continuation](../intg3a/README.md#include-sort-csv-and-fixed-coefficient-scoring) and fresh destinations. Those reviewer records and generated publications are retained separately. A new approval produces a different publication identity. The standalone candidate commands in [VALIDATION.md](VALIDATION.md) can demonstrate engineering behavior independently of the retained approval.

## Five skills and six goals

| Goal | Available and evidence | Missing deliverable or proof | Smallest next action without SAS |
| --- | --- | --- | --- |
| Reconstruction | Source-only evidence for bounded DATA, SQL, gates, SORT and logistic declarations. [TRACE/MAP](TRACE_MAP.md). | Attributable execution, cross-fragment version continuity and export behavior. | Review source boundaries and resolve business ownership of missing contracts. |
| Requirements | Draft PRD, module acceptance criteria and questions. [Requirements](REQUIREMENTS.md). | Owner-approved intent and a reference schema. | Review the requirements and agree on intended inputs, outputs and errors. |
| Optimization | Dependency-driven hypotheses. [Optimization](OPTIMIZATION.md). | Workload sizes, baseline and controlled measurements. | Agree on the workload and measurement protocol. |
| Alternative designs | Draft Python, Spark, Ray and Dask designs and ADRs. [Architecture](ARCHITECTURE.md). | Operational constraints, comparative results and a runtime decision. | Review correctness and deployment constraints before selecting a benchmark. |
| Migration and verification | Existing Python candidates and pinned engineering controls. [Validation](VALIDATION.md). | SAS descriptors and reference outcomes, fitted model and ODS. | Prepare the independent comparison scope; actual reference evidence needs authorized SAS access. |
| Final handoff | Manifest-bound draft and repeatable operator instructions. | Human acceptance of this draft and separate semantic acceptance. | Review this package and record decisions with its exact identity. |

Use `sas-reconstruct` for TRACE and data flow, `sas-specify` for the PRD and module specifications, `sas-analyze` for dependency and optimization hypotheses, `sas-validate` for reference and engineering proof obligations, and `sas-architect` for designs and ADRs. For a future manual Agent session, provide the exact bound evidence, review subject and candidate artifacts. Follow the [preflight and exact-byte approval procedure](../gate1/README.md#prepare-a-copilot-draft-for-review). File reads alone establish neither skill execution nor human approval.

## Package metadata

```text
artifact_authority: DRAFT
behavioral_evidence: UNAVAILABLE
semantic_verification: UNVERIFIABLE
semantic_acceptance: BLOCKED
reference_experiment: NOT_RUN
benchmark_execution: NOT_RUN
historical_source_run_provenance: UNBOUND
human_review: REQUIRED
```
