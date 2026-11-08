# Review a multi-file SAS modernization

Start with the [modernization review](REVIEW.md). This public synthetic project
builds a running balance and produces two separate datasets, one sorted and one
enriched. The review explains the reconstructed logic, the decisions you need
to make, and why candidate execution is unavailable for this project.

## Run the review offline

Use the repository's [Python 3.12 development environment](../../README.md)
and run from the repository root. Choose a fresh scratch directory and a fresh
destination for each run.

```sh
scratch=$(mktemp -d /tmp/sas-modernization-XXXXXX)
mkdir "$scratch/INTAKE"
cp examples/modernization/source/* "$scratch/INTAKE/"
python3.12 -IB scripts/review_intake.py --intake "$scratch/INTAKE" --inventory
python3.12 -IB scripts/review_intake.py --intake "$scratch/INTAKE" \
  --p2a --modernization-drafts --destination "/tmp/sas-re-int1-${scratch##*/}"
```

1. Check the inventory and the explicit [scope](source/scope.json). Discovery
   identifies the files but requires manual scoping for this project. The
   supplied scope declares the entry program, both literal include edges and
   exact file hashes. The [profile](source/profile.json) declares the typed
   synthetic inputs and input ordering. Use only approved public inputs.
2. Open the generated evidence and YAML drafts. Compare them with the
   [checked-in replay](evidence/README.md). The
   [package manifest](MANIFEST.json) binds this example's source, generated
   artifacts and authored review. A fresh run regenerates the evidence and
   handoff, while this example supplies the reviewed-for-evidence draft prose.
3. Review the pending ordering, multiplicity, business and runtime decisions
   in [migration-profile.yaml](evidence/migration-profile.yaml) and
   [tie-out.yaml](evidence/tie-out.yaml). The
   [five-skill handoff](evidence/MODERNIZATION_REVIEW.md) gives an optional,
   human-invoked Copilot workflow. The five review sections are available
   offline in [REVIEW.md](REVIEW.md).
4. Check candidate applicability before continuing. This subject ends at
   design review. For a separate eligible projection-and-sort project, follow
   the [operator approval and continuation guide](../intg1/README.md).
   Review and approval apply to the exact subject under consideration.

Human approval is pending. SAS reference and benchmark execution are
`NOT_RUN`, semantic verification is `UNVERIFIABLE`, and semantic acceptance
is `BLOCKED`.
