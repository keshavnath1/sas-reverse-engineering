# MOD-2 · Public reference-coded design and fixed scores

Use the existing Python 3.12 development installation on the supported
POSIX path. Reuse the pinned public preparation and population evidence
from the [MIG-5 instructions](../mig5/README.md). Choose a fresh destination.

```bash
python3.12 -IB scripts/score_prepared_logistic.py \
  --model-source examples/mod2/model.sas.txt \
  --model-source-sha256 0f6741a10b6fc29de02fdd9a4500c95f2cc948814d109c1643cfd893a7e58a4c \
  --preparation-evidence /private/tmp/sas-re-source-mig3-demo/EVIDENCE.json \
  --population-evidence /private/tmp/sas-re-source-mig4-demo/EVIDENCE.json \
  --scenario passes --destination /tmp/sas-re-mod2-demo
```

On Linux use the physical paths printed by the source-review receipts.
The command also accepts the original authorized ML-2 source using its
approved digest `fe1bbbd9e531d53103aad52caafbd616a8365e9bcc81241ffa466aaa1c218f85`.
It replays the existing recognizer over lines 417–441 for that profile.
Keep the original source and any resulting local review outside Git.
Both profiles score the same pinned public rows. Model text is read only.

Scoring uses full-mode Python candidate row ends in pre-sort order, only
on `PROCEED`. Each row's `case_id` and `id` are audit keys. A block or
upstream input refusal leaves both design and score files absent.

[MAPPING.json](MAPPING.json) maps the public numeric and character slots
positionally to the recovered non-CLASS and CLASS declaration orders.
The design starts with an intercept, then expands terms in MODEL order.
Public design column names use slots, and the plan records their source
names. The exact four-character aliases are mapped per field, with
`REFERENCE` mapped to the corresponding source reference declaration.
Other levels and their order are public fixture choices. The design omits
reference indicators and refuses unrecognized values, including missing
and nonfinite numbers. [COEFFICIENTS.json](COEFFICIENTS.json) supplies the
exact ordered public column names and finite coefficient values.

The event is the candidate's `Default=1`. The runner sums the coefficient
products with `math.fsum` and applies a sign-aware sigmoid. The two public
logits are 1.5 and 0.5. Probabilities are compared with an absolute
tolerance of 1e-15. This tolerance applies to engineering checks only.

Open `PLAN.json` for original evidence coordinates, design assumptions
and fixture hashes, and `VALIDATION.json` for engineering checks.
`DESIGN.json` and `SCORES.json` exist only when scoring runs. The manifest
binds these outputs to the evidence and public candidate inputs.

Fitting, convergence, and ODS production are `NOT_RUN`. Historical event
orientation, effective SAS CLASS columns, scoring equivalence, and dataset
continuity remain unverified. Authority stays `DRAFT`, behavioral evidence
`UNAVAILABLE`, semantic verification `UNVERIFIABLE`, acceptance `BLOCKED`,
reference and benchmark execution `NOT_RUN`, and provenance `UNBOUND`.
