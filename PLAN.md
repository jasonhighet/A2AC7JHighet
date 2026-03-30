# Investigator Agent Implementation Plan

## Overview
This document outlines the detailed plan to construct the Investigator Agent on a native Windows environment using Python 3.13.9. It serves to bridge the requirements in `STEPS.md` and the structural architecture prescribed in `PLAN_after.md`, adapting them specifically for the native Windows ecosystem and Gemini 1.5 Flash via the OpenAI-compatible endpoint.

## Technical Stack & Constraints
- **Language:** Python 3.13.9 (Native Windows). No WSL, Docker, or containers.
- **Package Manager:** `uv` ONLY. (`uv venv`, `uv add`). No `pip`, `uv pip`, or `requirements.txt`.
- **Frameworks:** LangChain v1.x and LangGraph.
- **Provider:** Google AI Studio (Gemini 1.5 Flash) via the OpenAI-compatible endpoint using `langchain-openai`.
- **Observability:** OpenTelemetry (exporting traces straight to local JSON) and LangSmith.
- **Testing:**
  - Files must use a `_test.py` suffix (e.g., `graph_test.py`).
  - Files must NOT have a `test_` prefix.
  - Unit tests co-exist in the same folder as the code under test.
  - Zero tolerance for failing tests, skipped tests, or deprecation warnings.
- **Architecture & Quality:**
  - Interfaces must use `Protocol` (no `ABC`).
  - Prioritise extreme decoupling and adhere strictly to DRY principles.
- **Spelling:** New Zealand English (e.g., initialise, organisation, prioritise, analyse).

## Project Structure
The repository will be initialised with this layout, mapped directly from `PLAN_after.md` but updated for our Gemini setup:

```text
investigator/
├── src/
│   ├── __init__.py
│   ├── agent/
│   │   ├── __init__.py
│   │   ├── graph.py             # LangGraph agent workflow (Gemini via OpenAI endpoint)
│   │   ├── state.py             # Agent state schema (TypedDict)
│   │   ├── prompts.py           # System prompts determining agent behaviour
│   │   ├── graph_test.py        # Unit tests
│   │   ├── state_test.py        
│   │   └── prompts_test.py      
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── jira.py              # JIRA metadata tool
│   │   ├── jira_test.py
│   │   ├── analysis.py          # Test metrics analysis tool
│   │   └── analysis_test.py
│   ├── observability/
│   │   ├── __init__.py
│   │   ├── tracer.py            # OpenTelemetry JSON export config
│   │   ├── callbacks.py         # LangChain callbacks for tracing
│   │   ├── exporter.py          # File span exporter (Windows path compliant)
│   │   └── tracer_test.py
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── config.py            # Pydantic settings
│   │   ├── file_utils.py        # File readers (pathlib based)
│   │   └── config_test.py
│   └── evaluation/
│       ├── __init__.py
│       ├── runner.py            # LangSmith evaluation executor
│       ├── scenarios.py         # Dataset creation
│       ├── evaluators.py        # Custom evaluator functions
│       ├── evaluators_test.py
│       └── runner_test.py
├── tests/                       # Integration tests ONLY
│   ├── __init__.py
│   ├── integration/
│   │   ├── __init__.py
│   │   ├── agent_end_to_end_test.py
│   │   └── tools_integration_test.py
│   └── fixtures/
│       └── sample_data.py
├── traces/                      # Local OpenTelemetry JSON traces
├── incoming_data/               # Provided feature test/JIRA data
├── cli.py                       # CLI interface for agent
├── pyproject.toml               # Built via uv
├── .env                         # Config variables
├── .env.example                 # Config template
├── .gitignore
└── README.md
```

## Implementation Steps

### Step 1: UI Setup, Agent Configuration & Conversations
1. **Initialise Workspace:**
   - Execute `uv venv` to create the virtual environment on Windows.
   - Use `uv add langchain langgraph langchain-openai pydantic pydantic-settings python-dotenv pytest` to establish dependencies.
2. **Environment Variables Config:**
   - Set up `.env` with `GEMINI_API_KEY`, replacing Anthropic configuration.
   - Configure Pydantic `Settings` in `src/utils/config.py`.
3. **Agent Core via Gemini:**
   - Set up `ChatOpenAI` from `langchain-openai` but configure `base_url="https://generativelanguage.googleapis.com/v1beta/openai/"` and `model="gemini-1.5-flash"`.
   - Build the base LangGraph `StateGraph` in `src/agent/graph.py` with the initial prompts.
4. **CLI REPL:**
   - Build `cli.py` to allow the user to have a continuous conversational loop with the agent.
5. **Validation:**
   - Write `_test.py` files to ensure all graphs, configs, and states compile correctly and pass seamlessly.

### Step 2: Feature Lookup Tool & Error Handling/Persistence
1. **JIRA Tool:**
   - Implement `get_jira_data` in `src/tools/jira.py` to read `incoming_data/feature*/jira/feature_issue.json`. Ensure native Windows path usage through `pathlib`.
2. **Tool Binding:**
   - Update `src/agent/graph.py` to bind tools to the Gemini LLM. Ensure Gemini's tool usage aligns with OpenAI-compatible endpoint capabilities.
   - Integrate LangGraph `ToolNode` into the agent's graph to handle routing.
3. **Persistence:**
   - Instead of saving purely to memory, serialise the conversational state to a JSON file per session (e.g., `traces/conv_YYYYMMDD_...json`) after each turn.
4. **Validation:** Ensure `jira_test.py` runs natively and handles Windows paths securely.

### Step 3: Testing Metrics Results Tool
1. **Analysis Tool:**
   - Create `get_analysis` inside `src/tools/analysis.py` to target `metrics/unit_test_results.json` and `metrics/test_coverage_report.json`.
2. **Decision Engine Details:**
   - The agent should use prompt orchestration to decide if a feature is ready for its progressive phase based purely on passing tests (zero failure tolerance).
3. **Validation:** Testing must thoroughly replicate the "feature with failure" vs. "clean feature" paradigms described in `STEPS.md`.

### Step 4: Observability Tracing
1. **OpenTelemetry Installation:**
   - Run `uv add opentelemetry-api opentelemetry-sdk`.
2. **Tracing Configuration:**
   - Set up a tracer in `src/observability/tracer.py` using a `ConsoleSpanExporter` redirected to JSON files over the native Windows filesystem.
3. **Integration:** Implement LangChain's callback handler to trap metrics like latency, LLM tool usage, and agent decision tree spans.
4. **Validation:** Verify comprehensive JSON payloads are deposited in the `traces/` folder.

### Step 5: Retry with Exponential Back-off
1. **Langchain Native Retries:**
   - Customise LLM instantiation with `Runnable.with_retry()` configuration to handle network or API transient failures.
   - Apply `with_retry()` selectively around tool invocations to recover from filesystem locks or temporary permission anomalies on Windows.
2. **Validation:** Use unit test mocks to mimic `ConnectionError` and prove exponential back-off triggers.

### Step 6: Evaluations
1. **LangSmith Integration:**
   - Install `uv add langsmith`. Config the `.env` with LangSmith keys.
2. **Dataset Creation:**
   - Create dataset logic inside `src/evaluation/scenarios.py` with 8+ diverse permutations testing happy paths, ambiguities, and zero-tolerance failing requirements.
3. **Custom Evaluators:**
   - Construct evaluators inside `src/evaluation/evaluators.py` specifically measuring feature identification accuracy, correct tool pipeline usage, and decision rationale.
4. **Validation:** Expose `--eval` within `cli.py` to trigger evaluations and ensure >85% success threshold across local tests natively tracked within LangSmith's dashboard.

## Procedural Rules
- Proceed one step at a time.
- Verify fully before advancing to the subsequent step.
- Ask for user clarification when faced with an ambiguous architectural fork.
