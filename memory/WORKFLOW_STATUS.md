# Collaboration Contract: Workflow & Status

> This document is the **binding agreement** for how we work together.  
> No stage is optional. No stage may be skipped. Quality over speed.

---

## Active Work Item

> 📄 **None** — pick the next item and update this pointer.
>
> Format: `changes/NNN-story_name.md` (e.g. `changes/001-first_story.md`)

---

## The 4-Stage Loop

Every piece of work passes through the following four stages, in order. Moving backwards is allowed; skipping forward is not.

```
[1. Task Planning] ──► [2. Build & Assess] ──► [3. Reflect & Adapt] ──► [4. Commit & Pick Next]
        ▲                                                                          │
        └──────────────────────── (next story) ───────────────────────────────────┘
```

---

### Stage 1 — Task Planning

**Purpose**: Agree on *what* we are building and *how* before a single line of code is written.

| | |
|---|---|
| **Inputs** | A candidate story/feature idea |
| **Outputs** | A populated work item file (e.g. `changes/001-first_story.md`) with a clear Goal, agreed Approach, and signed-off Acceptance Criteria checklist |

**Activities**
- Create the work item file using `changes/TEMPLATE.md`
- Write a single-sentence **Goal** — the "definition of done"
- Decompose the goal into specific, testable **Acceptance Criteria** (`- [ ]` checklist)
- Agree on the **Approach** (files to touch, patterns to follow, constraints from `TECHNICAL.md`)
- Update the **Active Work Item** pointer at the top of this file

**Transition Protocol — Gate: Planning → Building**

> ✅ The following must all be true before Stage 2 begins:
> - The work item file exists and is committed (or staged)
> - Every Acceptance Criterion is written as a specific, verifiable statement
> - The Approach is agreed by both parties (no surprises)
> - Any ambiguities or blockers are documented in the work item's `## Notes` section

---

### Stage 2 — Build & Assess

**Purpose**: Implement the agreed plan. Run all tests. Produce evidence of correctness.

| | |
|---|---|
| **Inputs** | A fully completed Stage 1 work item (see gate above) |
| **Outputs** | Working code/docs, all tests passing, Acceptance Criteria checked off |

**Activities**
- Implement changes strictly within the agreed Approach
- Write or update tests alongside the code (not after)
- Run the full test suite — see `memory/ENV_SCRIPTS.md` for commands
- Check off each Acceptance Criterion (`- [x]`) only when verified by a passing test or explicit manual confirmation
- Update the work item `## Status` field to `Building`
- Document any deviations from the plan in `## Notes / Blockers`

**Transition Protocol — Gate: Building → Reflecting**

> ✅ The following must all be true before Stage 3 begins:
> - All `pytest` tests pass (config-service): **zero failures, zero errors**
> - All `vitest` tests pass (ui): **zero failures, zero errors**
> - Every Acceptance Criterion is checked off (`[x]`)
> - No unapproved dependencies were introduced (see `TECHNICAL.md`)
> - The AI has shown the test output as evidence — "it works" is not sufficient

---

### Stage 3 — Reflect & Adapt

**Purpose**: Step back. Review the actual output against the intent. Catch what the tests don't.

| | |
|---|---|
| **Inputs** | Passing build from Stage 2 |
| **Outputs** | A decision: **Ship it** or **Adapt** (with specific changes noted) |

**Activities**
- Review the diff/changes for code quality, naming clarity, and adherence to our architecture
- Check documentation was updated where necessary (e.g. `ARCHITECTURE.md`, docstrings, API specs)
- Ask: *"If a new developer read this code tomorrow, would it be clear?"*
- If issues are found: document them in the work item's `## Notes` section, return to Stage 2
- Update the work item `## Status` field to `Reflecting`

**Transition Protocol — Gate: Reflecting → Committing**

> ✅ The following must all be true before Stage 4 begins:
> - Both parties are satisfied with the quality of the output
> - Any documentation that should be updated, has been updated
> - The work item file itself is accurate and complete

---

### Stage 4 — Commit & Pick Next

**Purpose**: Persist the work cleanly and prepare for the next story.

| | |
|---|---|
| **Inputs** | A "Ship it" decision from Stage 3 |
| **Outputs** | A clean git commit; the Active Work Item pointer updated to `None` (or the next story) |

**Activities**
- Commit with a clear, conventional commit message (e.g. `feat: add X`, `fix: resolve Y`)
- Mark the work item `## Status` as `Done`
- Archive: leave the work item file in `changes/` — do not delete it (it is the audit trail)
- Update the **Active Work Item** pointer at the top of this file to `None` or the next story
- Choose the next story and begin Stage 1

---

## Work Item File Structure

All active stories and features are tracked as individual Markdown files in the `changes/` directory.

### Naming Convention

```
changes/NNN-story_name.md
```

- `NNN` — zero-padded sequential number (e.g. `001`, `002`, `042`)
- `story_name` — lowercase words separated by underscores, max 4 words (e.g. `001-first_story.md`, `042-add_app_endpoint.md`)

### Template

See [`changes/TEMPLATE.md`](../changes/TEMPLATE.md) for the blank template to copy.

### Required Sections

| Section | Purpose |
|---|---|
| `## Goal` | One sentence — the definition of done |
| `## Acceptance Criteria` | Testable `- [ ]` checklist; checked off only when verified |
| `## Approach` | Agreed implementation strategy (from Stage 1) |
| `## Status` | Current stage: `Planning` / `Building` / `Reflecting` / `Done` |
| `## Notes / Blockers` | Deviations, discoveries, open questions |

> **Rule**: Status lives in the work item file only. Do not duplicate it here.  
> **Rule**: This file only holds the pointer to the active work item.

---

## Acceptance Criteria Rules

1. **Specific**: "The `GET /apps` endpoint returns a 200 with a list of apps" — not "the endpoint works"
2. **Verifiable**: Each criterion must be provable via a test or an explicit manual check step
3. **Atomic**: One concern per criterion — no "and" criteria
4. **Checked with evidence**: A criterion is only marked `[x]` after a test passes or both parties confirm manually

---

## Build & Test Protocol

> 🚫 **Non-negotiable. No exceptions.**

- Tests are written **alongside** the code, not after
- A build is not "done" until the full test suite runs clean — partial passes are failures
- The AI **must show the test output** when declaring Stage 2 complete
- All commands are sourced from [`memory/ENV_SCRIPTS.md`](./ENV_SCRIPTS.md)

| Layer | Command | Must Pass |
|---|---|---|
| Python (config-service) | `uv run pytest` | All tests, zero failures |
| TypeScript (ui) | `pnpm test` | All tests, zero failures |

---

## See Also

- [`memory/TECHNICAL.md`](./TECHNICAL.md) — Stack constraints and approved dependencies
- [`memory/ARCHITECTURE.md`](./ARCHITECTURE.md) — Layered architecture and service boundaries
- [`memory/ENV_SCRIPTS.md`](./ENV_SCRIPTS.md) — All dev commands and environment setup
- [`memory/ABOUT.md`](./ABOUT.md) — Project purpose and domain context
