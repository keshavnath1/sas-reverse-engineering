# SAS Modernization — Skills First

**Understand the SAS workload. Recover its requirements. Propose a better design.**

This branch is the clean team workspace. Add your authorized SAS programs and supporting files to `intake/`, then ask Copilot or Codex to produce a readable draft package. The AI assistant does the analysis through focused skills; there is no parser installation, migration engine or collection of demo runners to navigate.

```text
Your SAS intake
      ↓
Understand → Specify → Design → Review → Package
      ↓
Requirements + architecture + validation plan for human review
```

We are not translating SAS line by line. We first recover the business rules and dependencies, then compare better Python or distributed designs without losing required behavior. Correctness must later be proved by SAS tie-out; optimization must later be proved by representative benchmarks.

## Read these three files

- **[README.md](README.md):** what the team does and what it receives.
- **[DESIGN.md](DESIGN.md):** why we built this workflow, its roles and decisions.
- **[AGENTS.md](AGENTS.md):** the instructions the AI must follow.

Everything else supports that story. No historical run evidence, candidate implementations, test suite or milestone archive is shipped in this branch's current tree. Existing history and the original branches are preserved; this is not history deletion or a replacement for the engineering runtime.

## Start in three steps

1. Clone this clean branch, then open its **repository root** in your approved VS Code Copilot Agent Mode or Codex environment:

   ```sh
   git clone --branch design/skills-first-team --single-branch --depth 1 https://github.com/keshavnath1/sas-reverse-engineering.git sas-design
   cd sas-design
   ```

2. Add authorized SAS programs, includes, logs, LST files and available reference outputs under `intake/`. Optional: add `intake/context.md` with the goal, entry point and platform constraints. No separate scope/profile JSON is required.
3. Send:

> Read AGENTS.md. Use the orchestrate skill to inspect intake/ and generate a draft modernization package. Continue through the drafting stages; stop for critical missing evidence or final human review.

In Copilot, you may select `/start-design`. In Codex, you may use `$orchestrate` where skill selection is supported. If skill discovery is unavailable, ask the assistant to read `.agents/skills/orchestrate/SKILL.md` explicitly.

Routine drafting continues without approval after every document. Human choices, host tool permissions and final review remain human-owned. If `intake/` is empty, the agent stops and tells you what to add.

## What the skills do

**orchestrate** coordinates the run. **understand** reads SAS behavior and records facts and unknowns. **specify** drafts requirements and module contracts. **design** compares execution options and defines how to prove them. **review** challenges the drafts against original input in a fresh context where available. **package** produces a short team reading guide and handoff.

These are roles and instructions for your existing AI assistant, not six running services. There is one shared set of skill files under `.agents/skills/`. Optional Copilot author/reviewer profiles are conveniences, not proof of independence.

## What you receive

Each run gets a new private `output/<run-id>/` folder. Start with `START_HERE.md`.

```text
START_HERE.md          One-page explanation, recommendation and open decisions
SOURCE_EVIDENCE.md     What the SAS source and attributable logs support
SOURCE_MANIFEST.json  Optional computed file hashes; integrity only
PRD.md                Draft goals, business rules and capability map
MODULES.md            Draft module inputs, outputs and invariants
ARCHITECTURE.md       As-is/to-be diagrams, HLD and a concise LLD outline
adrs/                 Candidate decisions, tradeoffs and proof obligations
VALIDATION_PLAN.md    Proposed correctness, tie-out and benchmark checks
REVIEW.md             Source-aware reviewer findings and actual review context
HANDOFF.md            Draft package for downstream human review
PROGRESS.md           Stage, role, output, limitations and next action
```

All requirements and architectures are **DRAFT**. `READY_FOR_HUMAN_REVIEW` means a reviewed document package, not a completed migration. The agent must not select a runtime, invent an oracle or tolerance, generate approved configuration, execute SAS or claim a speedup.

## Small repository, clear responsibilities

```text
README.md + DESIGN.md        Team story and core architecture
AGENTS.md                    Agent roles, read order and stop rules
.agents/skills/              Six focused instruction files
.github/agents/ + prompts/   Thin Copilot entry points
intake/                      Empty until you add private inputs
output/                      Empty until the agent creates a private run
scripts/input_snapshot.py   One optional file-hash helper; no SAS analysis
SECURITY.md                  Privacy and safe-use boundaries
```

The agent may use the helper to compute/check hashes if Python 3 is available. There is no dependency install for document drafting. This does not claim fully offline AI execution or tested Mac/Windows host integration; your assistant needs its configured model access.

`intake/` and `output/` contents are ignored by Git. Do not publish private inputs or generated findings. Ignore rules are not a privacy scanner. Read [SECURITY.md](SECURITY.md) before using sensitive material.
