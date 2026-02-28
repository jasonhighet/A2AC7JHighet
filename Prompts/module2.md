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