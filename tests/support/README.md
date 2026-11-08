# Shared test support

This package contains independent synthetic vectors and memory-only test doubles. Import these helpers as `support.cp2_vectors`, `support.dependency_vectors`, `support.preview_expectations`, and `support.windows_fake` under the standard `unittest discover -s tests` invocation. Their literal expected values, executable behavior, and existing annotations are unchanged; they do not establish independently accepted SAS semantics or native Windows qualification.

`paths.py` computes `REPOSITORY_ROOT` from this package's location and derives `FIXTURES_ROOT`. Tests use these paths to inspect checkout artifacts while importing production code from the prepared installation. Neither this package nor its path helper inserts checkout `src` into `sys.path`.

## Purposeful legacy exceptions

Six modules deliberately remain at their original `tests/` paths with their exact original bytes:

| Root module | Reason |
| --- | --- |
| `p2a_expectations.py` | Independently reviewed reconstruction declarations with asserted byte digests. |
| `mvp2_expectations.py` | Frozen multimodule source and input declarations used by historical review scripts. |
| `mvp3_cases.py` | Hash-bound behavioral case table and original independent expectations. |
| `p2a_support.py` | Historical script adapter used directly by review commands and scratch-clone replay. |
| `mvp2_fixture.py` | Historical multimodule fixture adapter used by script consumers and copied replay roots. |
| `fixture_support.py` | Existing evidence fixture adapter retained unchanged for the first refactor. |

These are real preserved modules, not shim aliases or duplicate implementations. Tests continue to import them by their original top-level module names because unittest discovery adds `tests/` to its import path. Their preservation avoids changing historical scripts, fixture authority, copy-replay digests, and frozen rendered links. Keep `tests/fixtures/` byte-identical as well.
