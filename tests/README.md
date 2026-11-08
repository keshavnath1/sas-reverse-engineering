# Test layout and execution

Tests are grouped by the behavior they protect rather than implementation checkpoints. Category packages have empty initializers; discovery uses standard-library `unittest`, with no custom loader or additional framework.

| Location | Coverage |
| --- | --- |
| `core/` | Contracts, evidence identity and integrity, authorization, parsing, inventory runs, installed CLI, and baseline checks. |
| `reconstruction/` | Graph facts, independently reviewed public reconstruction, reconstruction publication, dependency diagnostics, previews, behavioral tieout, and decision review. |
| `workflow/` | Intake, source and operator review, claim gates, planning, migration candidates, preparation/population gates, scoring, running balance, and repository skill contracts. |
| `platform_checks/` | Backend capabilities, adversarial filesystem publication, POSIX descriptors, memory-only Windows protocols and native-call doubles, and workstation process boundaries. |
| `support/` | Independent vectors, shared checkout paths, and memory-only test doubles. |
| `fixtures/` | Immutable public synthetic source, evidence, and candidate-execution fixtures. |

## Discovery and installation

From the repository root, use the prepared Python 3.12 environment:

```sh
python -m unittest discover -s tests -v
```

For installed-wheel validation, build and install the wheel using the repository's documented procedure, then run discovery outside the checkout:

```sh
CHECKOUT=/absolute/path/to/checkout
cd /tmp
python -m unittest discover -s "$CHECKOUT/tests" -v
python -c 'import sas_re; print(sas_re.__file__)'
```

The final path must identify installed `site-packages`, not checkout `src`. `support.paths` computes the checkout and fixture roots relative to its own file without modifying the production import path. Existing script integration tests may add the checkout's `scripts/` directory to import historical development commands; they must not add checkout `src`.

Unittest adds the discovery root `tests/` to its import path, so shared helper imports use `support.*`, and cross-test imports use category-qualified module names such as `workflow.test_review_workflow` and `platform_checks.test_platform_io`. Do not add root test-module aliases or shim packages. Import and patch relocated private implementation modules through their owning `sas_re._filesystem` or `sas_re._review` namespace; root review facades are historical script boundaries, not owners of implementation globals.

The platform category is deliberately named `platform_checks/`, not `platform/`. The latter shadows Python's standard-library `platform` under the unchanged discovery command and breaks native adapters and dependencies such as `jsonschema`. The non-conflicting name preserves ordinary imports without shims, preloading tricks, or custom loaders.

## Preserved authority and bytes

This refactor changes organization, import namespaces, and path resolution only. It does not change schemas, fixture bytes, literal expected rows, tolerances, counts, case declarations, checkpoint strings inside protocol records, or authority statuses. The three hash-bound expectation/case modules and three historical adapter helpers remain at their original paths and bytes; [the support README](support/README.md#purposeful-legacy-exceptions) explains these intentional exceptions.

Windows unit fixtures and simulated selection tests do not qualify native Windows I/O. Synthetic candidates and behavioral controls do not establish SAS equivalence or promote `DRAFT`, `UNVERIFIABLE`, `BLOCKED`, or `NOT_RUN` records. Frozen rendered links and stage basename tracing remain unchanged.
