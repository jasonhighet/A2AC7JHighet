# Rule: Project Memory Auto-Load

## Context
To ensure consistent architectural follow-through and prevent hallucinations regarding project constraints, the agent must always be aware of the "Project Memory".

## Instructions
At the start of every session or when beginning a new major task, the agent MUST read the following files:
- [ABOUT.md](file:///e:/Github/HyprCourse/Project/memory/ABOUT.md): Project overview and personas.
- [TECHNICAL.md](file:///e:/Github/HyprCourse/Project/memory/TECHNICAL.md): Strict technical constraints (No ORM, Windows-native, etc.).
- [ARCHITECTURE.md](file:///e:/Github/HyprCourse/Project/memory/ARCHITECTURE.md): Service boundaries and data management decisions.
- [ENV_SCRIPTS.md](file:///e:/Github/HyprCourse/Project/memory/ENV_SCRIPTS.md): Environment variables, dev commands (`uv`, `pnpm`, Makefile targets).
- [WORKFLOW_STATUS.md](file:///e:/Github/HyprCourse/Project/memory/WORKFLOW_STATUS.md): Collaboration contract — 4-stage workflow, active work item pointer, and build/test protocol.

Do not proceed with implementation or architectural advice without first confirming the state of these documents. Always check WORKFLOW_STATUS.md to identify the active work item before starting any build work.
