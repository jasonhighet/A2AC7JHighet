# Investigator Agent Implementation Plan (LangChain + Python) - Module 8

## Overview

Python + LangChain v1.x implementation of the Feature Readiness Investigator Agent for Module 8. This document covers **how** to build the expanded agent with comprehensive retrieval and context management capabilities in a Windows environment.

**Module 8 Focus**: Agentic Knowledge Management & Context Window Management.

## Technical Stack & Constraints

- **Language**: Python 3.13.9 (managed via `uv`).
- **Package Manager**: `uv` only (no `pip` or `requirements.txt`).
- **Frameworks**: LangChain v1.x and LangGraph.
- **Provider**: Google AI Studio (Gemini 1.5 Flash) via the OpenAI-compatible endpoint.
- **Search Strategy**: `ripgrep` (installed on system) for document searching via Python `subprocess`.
- **Environment**: Native Windows ("on the metal"), no Docker or containers.
- **Spelling**: New Zealand English (e.g., initialise, organisation, prioritise).

## Implementation Constitution

- **Tests**: Unit tests must be in the same folder as the code under test, use a `_test.py` suffix, and must NOT have a `test_` prefix.
- **Interfaces**: Use `Protocol`; do NOT use `ABC`.
- **Quality**: No failing tests, skipped tests, or deprecation warnings are allowed.
- **Decoupling**: Prioritise clean decoupling and DRY principles.
- **Memory**: Utilise `ConversationSummaryMemory` to manage context window pressure.

## Project Structure

```
investigator/
├── src/
│   ├── agent/
│   │   ├── graph.py             # LangGraph workflow definition
│   │   ├── state.py             # Agent state (TypedDict)
│   │   ├── prompts.py           # System prompts with NZ English
│   │   ├── memory.py            # (NEW) ConversationSummaryMemory setup
│   │   ├── memory_test.py       # (NEW)
│   │   └── ...
│   ├── tools/
│   │   ├── analysis.py          # (EXPAND) 8 analysis types (5 metrics + 3 reviews)
│   │   ├── planning.py          # (NEW) list, read, search_planning_docs (ripgrep)
│   │   ├── planning_test.py     # (NEW)
│   │   └── ...
│   ├── observability/
│   │   ├── tracer.py            # OpenTelemetry tracing for new tools/memory
│   │   └── ...
│   └── evaluation/
│       ├── scenarios.py         # (UPDATE) Module 8 retrieval scenarios
│       ├── evaluators.py        # (UPDATE) Comprehensive retrieval evaluators
│       └── ...
├── incoming_data/               # Test data (metrics, reviews, planning docs)
├── cli.py                       # CLI for manual verification
├── .env                         # Gemini & LangSmith configuration
└── pyproject.toml               # uv project definition
```

## Detailed Roadmap

### Step 1: Comprehensive Metrics Analysis

**Goal**: Expand the analysis tool from 2 to 5 metric types.

- **Tasks**:
    - Update `src/tools/analysis.py` to recognise `pipeline_results`, `performance_benchmarks`, and `security_scan_results`.
    - Update `src/agent/prompts.py` with specific decision criteria for these metrics.
    - Write unit tests in `src/tools/analysis_test.py` for each new metric type.
- **Verification**: Agent successfully retrieves and cites pipeline results when asked about production readiness.

### Step 2: Review Analysis Tools

**Goal**: Add support for 3 review types (security, UAT, stakeholder approvals).

- **Tasks**:
    - Update `src/tools/analysis.py` to handle `reviews/security`, `reviews/uat`, and `reviews/stakeholders`.
    - Enhance `src/agent/prompts.py` to incorporate human review outcomes into the final readiness decision.
    - Add blocking logic: Progress must be halted if security shows HIGH risk.
- **Verification**: Agent blocks progression to production if stakeholder approvals are pending.

### Step 3: Planning Document Tools (Ripgrep)

**Goal**: Implement tools to list, read, and search planning documentation via ripgrep.

- **Tasks**:
    - Implement `list_planning_docs` to show available `.md` files in `incoming_data/{feature}/planning/`.
    - Implement `read_planning_doc` for full-text retrieval (used sparingly).
    - Implement `search_planning_docs` utilising `subprocess.run(["rg", "--json", ...])` to find specific requirements.
    - **Strategy**: Confirm `rg.exe` location on Windows and ensure it's utilised correctly without shell injection risks.
- **Verification**: Agent uses `search_planning_docs` instead of reading the entire `DESIGN_DOC.md` when asked for specific acceptance criteria.

### Step 4: Context Window Management

**Goal**: Implement `ConversationSummaryMemory` to prevent context overflow.

- **Tasks**:
    - Create `src/agent/memory.py` to initialise the summarisation memory.
    - Integrate memory into the `LangGraph` state in `src/agent/graph.py`.
    - Set a `max_token_limit` (e.g., 2000 tokens) to trigger summarisation of early turns.
- **Verification**: Agent maintains coherence over a long conversation involving multiple large document reads.

### Step 5: Update Observability

**Goal**: Ensure tracing captures all new tool operations and memory summarisation.

- **Tasks**:
    - Add OpenTelemetry spans to the new planning tools in `src/tools/planning.py`.
    - Log document sizes and ripgrep match counts in trace attributes.
    - Track memory summarisation events in the agent workflow.
- **Verification**: Inspect generated trace JSONs to confirm all tool calls and memory operations are recorded.

### Step 6: Update Evaluations

**Goal**: Adapt the evaluation suite to assess comprehensive retrieval and tool selection.

- **Tasks**:
    - Add Module 8 scenarios to `src/evaluation/scenarios.py` (e.g., assessing features with large doc volumes).
    - Implement `evaluate_comprehensive_retrieval` in `src/evaluation/evaluators.py`.
    - Run evaluations via `uv run python src/evaluation/runner.py`.
- **Verification**: Achieve >75% pass rate on retrieval and context management scenarios.

## Ripgrep Verification (Windows)

We will invoke `ripgrep` using the following Python pattern:

```python
import subprocess
import json

def invoke_ripgrep(query: str, path: str):
    # Ensure rg is in PATH or specify absolute path
    result = subprocess.run(
        ["rg", "--json", query, path],
        capture_output=True,
        text=True,
        check=False
    )
    # Parse result.stdout for JSON match entries
    ...
```

## NZ English Dictionary

- Initialise / Initialisation
- Organisation / Organisational
- Prioritise / Prioritisation
- Centralise / Centralisation
- Analyse / Analysis (noun remains analysis)
- Utilise / Utilisation
