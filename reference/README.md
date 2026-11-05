# Approved specification baseline

`Codex_SAS_Architecture_Pack_v2.zip` is copied byte-for-byte from the user-supplied
archive. SHA-256:

`e3cbf3d9df6cc20c594261556c5e3ea1dfc292c9c1a30672c2d7b1a736b9718e`

The package metadata at `src/sas_re/data/baseline.json` is the machine-readable
baseline. The repository guard checks this archive against it. Do not regenerate
the pack manifest or execute its verification script during foundation checks.

The archive contains proposed contracts and example outcomes, not implemented
product schemas or executed tests. Its `docs/02_ARCHITECTURE_AND_WORKFLOW.md`
governs workflow and `docs/05_HANDOFF_AND_CONFIG.md` governs compatibility.

One ZIP entry has a misencoded Unicode filename for the early-discovery audit.
Step 1 matched all 26 manifest hashes by explicitly decoding that entry name from
CP437 to UTF-8. P0 preserves the original archive, avoiding a silently renamed or
rewritten baseline. Review the planning documents for the complete source catalog.
