# Run the public running-balance candidate

This draft engineering package implements the exact public project in the
[INTAKE modernization example](../sas-modernization/README.md). Start there to
replay reconstruction from the three SAS files. The
[requirements, TRACE/MAP, design and ADR](../../tests/fixtures/running-balance-workload/REVIEW.md) and the
[migration profile](../../tests/fixtures/running-balance-workload/evidence/migration-profile.yaml) and
[tie-out draft](../../tests/fixtures/running-balance-workload/evidence/tie-out.yaml) retain their original
bytes and pending decisions.

From the repository root in the prepared Python 3.12 environment, run:

```sh
python3.12 -IB scripts/run_running_balance.py
python3.12 -IB -m unittest discover -s tests -p test_running_balance.py
```

The [runner](../../scripts/run_running_balance.py) verifies the published
package manifest and every listed payload before using the bound synthetic
input profile. `--package` can select a byte-identical copy. It emits JSON
with three datasets, input evidence identities, and original graph pointers.
The source review is pinned to package manifest SHA-256
`cdf18e8c860931eef0e537986184c274a134811eb0909ac97393ec6774caef73`.
The command executes the draft candidate on public rows. Engineering
comparison runs separately in the tests.

## Provisional engineering decisions

| Stage | Implementation and boundary |
| --- | --- |
| Preparation | Read typed rows in declared ascending `group, subkey` order and reject decreasing keys. On the first row of a group reset retained balance to zero, then add amount with ordinary missing contributing zero. Mark the last row of each key prefix. Advance a one-element LAG queue only on positive amounts, carry it across groups and emit missing when no assignment occurs. |
| Sorted output | Preserve full records and multiplicity. Use both declared keys, ordinary missing first, with stable input order on ties as a candidate policy. |
| Enrichment | Read the original prepared stream independently of SORT. Match ordinary missing keys under the synthetic profile policy and preserve duplicate matches. Apply the right-weight predicate after matching. Unmatched rows have missing right weight and fail the filter. The emitted order is deterministic for this runner and the comparison treats SQL output as a multiset. |
| Numeric domain | Use ordinary missing or bounded decimal lexemes exactly representable as binary fractions, with denominator dividing 1024 and magnitude at most 2²⁰. Accumulation outside the same magnitude is refused. JSON output uses numbers and nulls. Special missing values, nonrepresentable inputs and unsupported row shapes are refused. |

The runner is limited to 1,000 rows per input and at most 10,000 matched pairs
before filtering. It handles the recovered behavior of this fixture. Other
manifests, arbitrary SAS syntax, macro execution and distributed execution are
outside the candidate contract.

## Engineering tie-out

The [public tests](../../tests/test_running_balance.py) contain independently
specified expectations. The published profile produces three preparation rows,
three SORT rows and three enrichment rows. The enrichment multiset contains
two copies of `(1, 2, 3)` and one `(2, 4, 5)`, in group, balance, weight order.
The separate edge case checks a missing key, duplicate matches, missing and
nonpositive weights, an unmatched group, equal-key order, group resets and
queue behavior after skipped calls. Refusal checks cover changed evidence,
descending inputs, unsupported numbers, row shape and exceeded bounds. Two
command runs produce byte-identical JSON.

Business review remains pending for balance and marker intent, duplicate
policy, tie order and tolerances. An independent reference still needs the
bound source, typed inputs and operation-level outputs. Runtime selection
and any representative benchmark remain pending. The runner has no
approval-gated publication path. Existing GATE-1 and human approval
requirements still apply to any supported publication route.

Artifact authority is DRAFT. Behavioral evidence is UNAVAILABLE. SAS reference
and benchmark execution are NOT_RUN, semantic verification is UNVERIFIABLE,
semantic acceptance is BLOCKED, and historical provenance is UNBOUND.

## Run from a fresh INTAKE review

Follow the [offline INTAKE guide](../sas-modernization/README.md) to generate a
fresh evidence directory. Pass its canonical path and the original INTAKE
directory to the existing runner:

```sh
python3.12 -IB scripts/run_running_balance.py \
  --package /path/to/generated-evidence --intake /path/to/INTAKE
```

Both directories must match the exact supported public workload. The runner
checks the evidence manifest and its payloads, the original SAS files, scope
and typed profile, and any generated modernization drafts against the published
package identities. It accepts evidence with or without the complete draft set.
The output is identical to the published-package invocation. The outer
manifest SHA-256 identifies the supported workload in both cases.
