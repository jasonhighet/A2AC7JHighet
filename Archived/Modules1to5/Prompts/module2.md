Mission 1: Initialize the Memory Bank
-------------------------------------

**Instruction for Antigravity (Plan Mode):**

> "I am starting Module 2: Context Engineering. Please execute the following setup:
>
> 1.  Use PowerShell to create a `memory/` directory in the root.
>
>
> 2.  Create an empty `memory/ABOUT.md` file.
>
>
> 3.  Read the existing `README.md`, `prompts/1-web-api-specs.md`, and the `config-service/` code to understand the project.
>
>
> 4.  Propose a structured draft for `memory/ABOUT.md` that covers: **Project Name**, **Description**, **Target Personas** (developers/admin), and **Domain Context** (centralized config)."

**Next Step (Act Mode):** Once you approve the draft, tell the agent to write the file and commit it: `git add memory/ABOUT.md && git commit -m "docs: init project memory"`.

* * * * *

Mission 2: Codify Technical & Architectural Memory
--------------------------------------------------

**Instruction for Antigravity (Plan Mode):**

> "We need to capture our architectural decisions to ensure future sessions don't hallucinate.
>
> 1.  Create `memory/ARCHITECTURE.md` and `memory/TECHNICAL.md`.
>
>
> 2.  Populate `memory/TECHNICAL.md` with our strict constraints: **No ORM (psycopg2 only)**, **Windows-native PostgreSQL (no Docker)**, and **uv for package management**.
>
>
> 3.  Populate `memory/ARCHITECTURE.md` with the service boundaries and the decision to use a custom migration system."

* * * * *

Mission 3: Configure Antigravity Auto-Loading (The "Rule")
----------------------------------------------------------

In Antigravity, rules go in `.agent/rules/`. This replaces the `.clinerules` step from the course.

**Instruction for Antigravity (Act Mode):**

> "Configure a workspace rule to auto-load our memory.
>
> 1.  Create the directory `.agent/rules/` if it doesn't exist.
>
>
> 2.  Create `.agent/rules/memory.md`.
>
>
> 3.  Inside that file, write a rule that instructs the agent to always read `@memory/ABOUT.md`, `@memory/TECHNICAL.md`, and `@memory/ARCHITECTURE.md` at the start of any session to maintain context."

* * * * *

Mission 4: Verify and Journal
-----------------------------

To ensure the "Context Framework" is actually working:

1.  **Restart the Session**: Click the "New Chat" or "Reset Context" button in Antigravity.

2.  **The Test Prompt**:

    > "Based on our memory files, what are our strict rules regarding database access and the local environment?"

3.  **Verification**: If it correctly identifies **No ORM** and **Windows-Native/No-Docker**, the framework is successful.


PART 2

### hase 1: Establish the "Memory Update" Protocol

Before building the library, you need a way to keep your memory files current without manually rewriting them every time.

**Instruction for Antigravity (Act Mode):**

> "I want to establish a phrase for updating our memory bank. Whenever I say **'Sync Memory'**, I want you to:
>
> 1.  Review our current conversation for any new architectural decisions, technical constraints, or domain facts.
>
>
> 2.  Propose specific edits to `@memory/TECHNICAL.md`, `@memory/ARCHITECTURE.md`, or `@memory/ABOUT.md` to capture this new context.
>
>
> 3.  Do not apply the changes until I approve the plan."

* * * * *

### Phase 2: Exercise 5a - Planning the Web Client Library

This is a "Plan" session. You are creating a TypeScript library that other teams will use to talk to your Config Service.

**Instruction for Antigravity (Plan Mode):**

> "Based on our project context in `@memory/`, let's plan a **Web Client Library**.
>
> **Goal**: Create a TypeScript abstraction layer so other apps don't have to use `fetch` directly to talk to our API.
>
> **Constraints**:
>
> -   **Tech Stack**: TypeScript (matching our UI standards in `memory/TECHNICAL.md`).
>
>
> -   **Dependencies**: Use `pnpm` and follow the 'No Framework' rule (Vanilla TS).
>
>
> -   **Source of Truth**: Use `@config-service/svc/api/endpoints.py` to define the client methods.
>
>
> -   **IMPORTANT**: Do not use any `Makefile` targets for this plan.
>
>
> -   **IMPORTANT**: Keep the plan simple. Do not break it down into an elaborate task list yet.
>
>
>
> Please provide a high-level file structure for `ui/packages/config-client` and describe the core `ConfigClient` class interface."

* * * * *

### Phase 3: Exercise 5b - Observability (Optional but Recommended)

If you want to try the non-functional requirement, focus on **OpenTelemetry**.

**Instruction for Antigravity (Plan Mode):**

> "Create a lightweight plan to add **OpenTelemetry** support to the `config-service`.
>
> -   Focus only on basic HTTP instrumentation for our FastAPI endpoints.
>
>
> -   Ensure the plan respects our **uv** package management and **Python 3.13** environment.
>
>
> -   Do not implement yet; just provide the plan for the `memory/TECHNICAL.md` update."