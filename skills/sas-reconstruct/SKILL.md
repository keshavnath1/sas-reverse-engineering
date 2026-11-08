---
name: sas-reconstruct
description: Recover SAS transformations, state and dependencies from an authorized source review or evidence package.
---

# sas-reconstruct

1. Identify the entry point, authorized files or spans, and source hashes from the
   selected package. Check manifest and payload identity using the existing
   Python tools where available. State which checks actually ran.
2. Trace each operation's declared inputs, outputs, calculations, predicates,
   ordering, state, and control boundaries. Cite the original file, lines and
   byte span, or the exact graph record that carries them. Keep declared reads
   and writes separate from inferred relationships.
3. Return a TRACE/MAP summary with supported, partial, unsupported, and
   uninspected coverage. Surface unresolved includes, macros, descriptors,
   execution order and dataset versions. Use the
   [source subset guide](../../docs/SOURCE_RECONSTRUCTION_DESIGN.md) for supported forms.

For fresh evidence use the [operator guide](../../README.md). Native Windows
evidence I/O remains BLOCKED.

Follow the [repository rules](../../AGENTS.md). Use the selected authorized
package and cite its evidence. Keep drafts DRAFT, verification UNVERIFIABLE,
acceptance BLOCKED, and unperformed execution NOT_RUN.

## Reference material

For the original offline example, see [`MANIFEST.json`](../../examples/offline-review/MANIFEST.json), [`EVIDENCE.md`](../../examples/offline-review/EVIDENCE.md).

To replay that original public example on supported POSIX with an unused destination:

```bash
python3.12 -IB scripts/review_workflow.py --destination /tmp/sas-re-review
```
