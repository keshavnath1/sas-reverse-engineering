# INT-1 public synthetic folder review

Run from the repository root with the prepared Python 3.12 environment on a
supported POSIX workstation.

```bash
.venv/bin/python -IB scripts/review_intake.py \
  --intake examples/public-intake \
  --destination /tmp/sas-re-int1-first
```

The intake can be a byte-identical copy of the two public files in any
authorized folder, including one named INTAKE. Choose a fresh direct child of
system scratch for each destination. The receipt gives the output location
and exact manifest digest. The destination writer reserves the directory
exclusively and writes the manifest last.

This slice pins the approved scope file and checks the source digest declared
in it. The existing filesystem helpers enumerate files and read the approved
bytes. Extra files, changed scope or source bytes, unsafe paths, and existing
destinations cause refusal. The repository keeps the public fixture under a
text suffix to respect its raw SAS file exclusions. The command analyzes the
original fixture bytes under that name.

| Artifact | Purpose |
| --- | --- |
| MANIFEST.json | Identities of the two intake files and all three payloads, review status and Copilot status |
| EVIDENCE.json | Existing bounded source review records with original line and byte spans |
| README.md | Existing source review summary and coverage limits |
| MIGRATION_REVIEW.md | Existing TRACE/MAP presentation, draft requirements, behavioral proof obligations and conditional architecture considerations |

The scope selects DATA lines 1–5 and SORT lines 13–15. The existing interval
inventory inspects the intervening SQL and gate declarations. The DATA filter
at line 3 remains a cited unresolved transformation. The declared SORT
handoff retains execution uncertainty and unestablished reachability. The
review carries `DRAFT`, `UNAVAILABLE`, `UNVERIFIABLE`, `BLOCKED`,
`NOT_RUN`, and historical provenance `UNBOUND`.

## Existing workflows and coverage

- `sas-re discover` inventories files under an explicit authorized scope and
  writes a P1 store attempt. INT-1 reuses its bounded filesystem helpers and
  original-byte hashing with a pinned two-file scope.
- `scripts/review_source.py` reviews explicitly selected source ranges.
  INT-1 calls its existing DATA-to-SORT review with SQL-gate recovery.
- The source review owns the facts in EVIDENCE.json. The existing migration
  renderer projects them into TRACE and MAP. INT-1 assembles these files and
  hashes them in the manifest.
- `scripts/review_workflow.py` provides the fixed fixtures' PRD,
  architecture and ADR reports. INT-1 uses the migration review's requirements
  and architecture sections for its own source subject. See
  [the existing offline package](../examples/offline-review/README.md).
- The repository's five SKILL.md files and `.agents/skills` discovery link were
  verified previously for Codex. Their graph-bound workflows refer to different
  fixture packages. This slice uses a manual, file-guided Copilot review.

## Copilot handoff

**NOT_TESTED.** VS Code was present on the inspected workstation. Its extension
listing reported no GitHub Copilot extension and emitted a sandbox permission
error for its log directory. No working Copilot session or review was observed.
Automatic loading of the repository's skills in Copilot remains unverified.

In an authorized Copilot Chat session, add the four generated files named in
the table and the two approved public fixture files `pipeline.sas.txt` and
`scope.json`. Verify the manifest digest against the command receipt and check
the listed input and payload hashes before the review. Include the receipt
digest in the prompt. [VS Code file context instructions](https://code.visualstudio.com/docs/chat/copilot-chat-context)

> Review the attached public INT-1 package against its source and manifest.
> Return review notes citing original line ranges or TRACE byte anchors.
> Separate declared rules and dependencies from unresolved behavior. Identify
> the unsupported DATA statement, the SQL gate and the evidence needed to
> establish SORT reachability. Explain the conditions for native Python and a
> distributed implementation while keeping runtime selection open. Report any
> missing or inconsistent evidence. Preserve DRAFT, UNVERIFIABLE, BLOCKED and
> NOT_RUN. Treat your notes as proposals for human review.

The operator invokes the chat and checks the citations against the deterministic
package. The review command completes independently of that interaction.
