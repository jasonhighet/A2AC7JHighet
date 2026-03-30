# Investigator Agent Implementation Plan (LangChain + Python)

## Overview

Python + LangChain v1.x implementation of the Feature Readiness Investigator Agent. This document covers **how** to build the agent in Python - specific packages, project structure, testing approach, and implementation details.  


## Technical Stack

**Python 3.13.9** with async/await

The latest versions of each of these packages:

- **uv** for dependency and venv management
- **LangChain v1.0.5** for core framework
- **LangGraph v1.0.2** for agent orchestration (modern agentic workflow framework)
- **langchain-anthropic** for Anthropic Claude integration
- **LangSmith** for evaluation, tracing, and observability
- **OpenTelemetry v1.38.0** for local observability and tracing (JSON export)
- **Pydantic 2.12.4** for data validation and tool schemas
- **pydantic-settings 2.11.0** for configuration management
- **pytest v9.0.0** for testing
- **python-dotenv** for .env file support

## Implementation Goals
- Clear, readable Python code that shows exactly what's happening
- Anthropic Claude as primary LLM provider
- LangGraph for agent orchestration (modern graph-based agentic workflow)
- LangSmith for evaluation and observability (primary platform)
- OpenTelemetry for local trace export to JSON files (complementary)
- Retry mechanism with exponential backoff using LangChain's built-in `with_retry()`
- Tool calling using @tool decorator
- Conversation history management via LangGraph state management
- Evaluation using LangSmith's built-in platform (datasets, experiments, evaluators)

## Implementation Constitution
- Clear, readable Python code that shows exactly what's happening
- For interfaces, use Protocol, and DO NOT use an ABC
- Place unit tests in the folder as the code under test
- Unit tests have a `_test.py` suffix and DO NOT have a `test_` prefix
- The `/tests` folder should only contain integration tests and common test assets
- When you're running tests and Python scripts, remember that the `python` binary is in the virtual environment
- Use `uv venv` to create the venv and `uv add` when adding dependencies
- Never use `pip` or `uv pip` and never create `requirements.txt`
- Use a `.env` file (and the related `.env.example`) to manage configuration

## Expectations of Quality (IMPORTANT)
In terms of priorities, code quality is the most important. How does this translate into this implementation?

- We will never accept failing tests, skipped tests, deprecation warnings, or any linting errors/warnings. These should never be skipped or suppressed without the explicit agreement with the human user.
- The code has proper decoupling to ensure ease in future features, maintenance, and fault-finding.
- Code should not be duplicated except through explicit instruction with the human user. When you think you have identified a rare scenario where it makes sense to not adhere to DRY principles, ask the opinion of the human user for guidance about how to proceed.

## Implementation Steps
The recommended order of implementation is defined in [STEPS.md](STEPS.md). The phases of implementation you will define later in this document align with these progression of steps.

<instructions_for_ai_assistant>
Read @DESIGN.md and @STEPS.md. Complete the rest of this document with implementation steps that align to these design principles and order of operations. The design allows for flexibility in certain areas. When you have multiple options, ask the user what their preference is - do not make assumptions or fundamental design decisions on your own.

**Ensure intuitive validation**: The developers completing these steps are strongly encouraged to validate the acceptance criteria for each step via automated tests and manual verification BEFORE moving on to the next step. The end of each step should be verifiable with automated and manual tests.

After ensuring you have all of the user preferences needed to proceed, create a detailed implementation plan below.

</instructions_for_ai_assistant>


## Project Structure

```
investigator/
├── src/
│   ├── __init__.py
│   ├── agent/
│   │   ├── __init__.py
│   │   ├── graph.py             # LangGraph agent workflow definition
│   │   ├── state.py             # Agent state schema (TypedDict)
│   │   ├── prompts.py           # System prompts and templates
│   │   ├── graph_test.py        # Unit tests for agent graph
│   │   ├── state_test.py        # Unit tests for state
│   │   └── prompts_test.py      # Unit tests for prompts
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── jira.py              # get_jira_data tool
│   │   ├── jira_test.py
│   │   ├── analysis.py          # get_analysis tool
│   │   └── analysis_test.py
│   ├── observability/
│   │   ├── __init__.py
│   │   ├── tracer.py            # OpenTelemetry setup and configuration
│   │   ├── callbacks.py         # LangChain callbacks for tracing
│   │   ├── exporter.py          # JSON trace file exporter
│   │   └── tracer_test.py
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── config.py            # Pydantic settings for configuration
│   │   ├── file_utils.py        # File reading utilities
│   │   └── config_test.py
│   └── evaluation/
│       ├── __init__.py
│       ├── runner.py            # LangSmith evaluation runner
│       ├── scenarios.py         # Test scenario definitions and dataset creation
│       ├── evaluators.py        # Custom evaluator functions
│       ├── evaluators_test.py   # Unit tests for evaluators
│       └── runner_test.py
├── tests/
│   ├── __init__.py
│   ├── integration/
│   │   ├── __init__.py
│   │   ├── test_agent_end_to_end.py
│   │   └── test_tools_integration.py
│   └── fixtures/
│       └── sample_data.py       # Test data fixtures
├── traces/                      # Generated trace JSON files
├── data/incoming/               # Test data (already provided)
│   ├── feature1/
│   ├── feature2/
│   ├── feature3/
│   └── feature4/
├── cli.py                       # CLI interface for manual testing
├── pyproject.toml              # uv project configuration
├── .env                         # Configuration (gitignored)
├── .env.example                 # Example configuration template
├── .gitignore
└── README.md
```

## Implementation Guide by Step

This guide follows the order defined in [STEPS.md](STEPS.md) and builds incrementally with verification at each step.

---

### **Step 1: UI Setup, Agent Configuration & Conversations**

**Goal:** Set up a CLI to interact with the agent and configure basic agent behavior

**Tasks:**

#### 1.1 Project Initialization
- Create virtual environment: `uv venv`
- Initialize pyproject.toml with dependencies
- Create .env.example with required configuration variables
- Create .gitignore (ignore .env, __pycache__, traces/, .venv/)
- Create basic README.md

**Dependencies to add:**
```bash
uv add langchain langgraph langchain-anthropic pydantic pydantic-settings python-dotenv pytest
```

**Acceptance Criteria:**
- ✅ Virtual environment created successfully
- ✅ All dependencies install without errors
- ✅ .env.example documents all required config variables
- ✅ Project structure matches the layout above

---

#### 1.2 Configuration Management
**Files:** `src/utils/config.py`, `src/utils/config_test.py`, `.env.example`

**Implementation:**
- Create Pydantic Settings class for configuration
- Load from .env file using python-dotenv
- Validate required fields (ANTHROPIC_API_KEY, model name, temperature)
- Support optional fields (max_tokens, trace output directory)

**Configuration Variables:**
```python
# .env.example
ANTHROPIC_API_KEY=your_api_key_here
LANGSMITH_API_KEY=your_langsmith_api_key_here
LANGSMITH_PROJECT=investigator-agent
MODEL_NAME=claude-3-5-sonnet-20241022
TEMPERATURE=0.0
MAX_TOKENS=4096
TRACE_OUTPUT_DIR=traces/
```

**Acceptance Criteria:**
- ✅ Config loads from .env file
- ✅ Missing required fields raise clear validation errors
- ✅ Unit tests verify config loading and validation
- ✅ Config is type-safe with Pydantic

---

#### 1.3 Basic Agent Core (No Tools Yet)
**Files:** `src/agent/graph.py`, `src/agent/state.py`, `src/agent/prompts.py`, `src/agent/graph_test.py`, `src/agent/state_test.py`

**Implementation:**
- Create agent state schema using TypedDict (messages, conversation history)
- Create system prompt defining agent role and purpose
- Initialize ChatAnthropic with config
- Build LangGraph workflow with nodes: agent → (tools added in Step 2)
- Implement basic conversation loop using graph.invoke()

**System Prompt (Initial):**
```
You are the Investigator Agent for the CommunityShare platform.

Your role is to assess whether software features are ready to progress through
the development pipeline (Development → UAT → Production).

You help product managers and engineering teams make informed decisions about
feature readiness by analyzing:
- Feature metadata (JIRA tickets, status, context)
- Test metrics (unit tests, coverage, failures)
- Risk factors and blockers

When asked about a feature's readiness, you:
1. Identify which feature the user is asking about
2. Gather relevant data using available tools
3. Analyze the data against readiness criteria
4. Provide clear recommendations with reasoning

Be concise, helpful, and transparent about your analysis process.
```

**LangGraph Architecture:**
```python
# State definition (src/agent/state.py)
from typing import TypedDict, Annotated, Sequence
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]

# Graph definition (src/agent/graph.py)
from langgraph.graph import StateGraph, END
from langchain_anthropic import ChatAnthropic

def create_agent_graph(config):
    # Define the function that calls the model
    def call_model(state: AgentState):
        messages = state["messages"]
        response = llm.invoke(messages)
        return {"messages": [response]}

    # Build the graph
    workflow = StateGraph(AgentState)
    workflow.add_node("agent", call_model)
    workflow.set_entry_point("agent")
    workflow.add_edge("agent", END)

    return workflow.compile()
```

**Acceptance Criteria:**
- ✅ Agent state schema defined with TypedDict
- ✅ LangGraph workflow compiles without errors
- ✅ Agent responds to basic questions about its purpose
- ✅ Conversation loop works (send message, get response)
- ✅ Unit tests verify graph creation and invocation

---

#### 1.4 CLI Interface
**Files:** `cli.py`

**Implementation:**
- Create simple REPL interface
- Load configuration from .env
- Initialize LangGraph agent workflow
- Maintain state across conversation turns
- Accept user input and display agent responses
- Support exit command

**Usage:**
```bash
python cli.py

Investigator Agent CLI
Type 'exit' to quit

You: What do you do?
Agent: I help assess whether software features are ready to progress...

You: exit
Goodbye!
```

**Acceptance Criteria:**
- ✅ CLI starts without errors
- ✅ User can input questions and receive responses
- ✅ Exit command works cleanly
- ✅ Configuration errors show helpful messages

---

#### 1.5 Step 1 Validation

**Manual Testing:**
```bash
# Test 1: Agent explains its purpose
You: What do you do?
Expected: Agent explains feature readiness assessment role

# Test 2: Agent asks for clarification on vague queries
You: Is the payment feature ready?
Expected: Agent asks for more details (no tools yet, so can't look anything up)
```

**Automated Testing:**
```bash
# Run all unit tests
pytest src/ -v

# Expected: All tests pass, no warnings
```

**Success Criteria:**
- ✅ CLI runs and accepts input
- ✅ Agent responds conversationally
- ✅ Agent personality matches system prompt
- ✅ All unit tests pass with no deprecation warnings

---

### **Step 2: Feature Lookup Tool & Error Handling/Persistence**

**Goal:** Agent can look up feature metadata using JIRA tool

**Tasks:**

#### 2.1 Understand Test Data Structure
**Action:** Explore `incoming_data/` to understand JIRA file structure

**Key Observations:**
- 4 features: feature1/, feature2/, feature3/, feature4/
- Each has `jira/feature_issue.json` with metadata
- Need to map feature names → folder names → JIRA data

**Create mapping utility:**
```python
# src/utils/file_utils.py
def get_feature_folder_mapping() -> Dict[str, str]:
    """Maps feature IDs to folder names.

    Returns:
        Dict mapping feature_id → folder path
    """
    pass
```

---

#### 2.2 Implement JIRA Tool
**Files:** `src/tools/jira.py`, `src/tools/jira_test.py`

**Implementation:**
```python
from langchain_core.tools import tool
from typing import List, Dict
import json
from pathlib import Path

@tool
def get_jira_data() -> List[Dict]:
    """Retrieves metadata for ALL features from JIRA.

    Returns an array with: folder, jira_key, feature_id, summary, status,
    data_quality for each feature.

    Use this tool to:
    - Get a list of all available features
    - Find the feature_id needed for other tools
    - Understand current feature status
    """
    # Read from incoming_data/feature*/jira/feature_issue.json
    # Parse and return list of features
    pass
```

**Error Handling:**
- Missing JIRA files → return graceful error message in tool output
- Malformed JSON → log error, return partial data if possible
- Empty directory → return empty list with note

**Acceptance Criteria:**
- ✅ Tool retrieves all 4 features from test data
- ✅ Returns correct schema: folder, jira_key, feature_id, summary, status
- ✅ Handles missing files gracefully
- ✅ Unit tests verify tool behavior with mock data
- ✅ Unit tests verify error handling

---

#### 2.3 Integrate JIRA Tool into Agent
**Files:** `src/agent/graph.py`, `src/agent/prompts.py`

**Implementation:**
- Bind `get_jira_data` tool to ChatAnthropic model
- Add conditional edge for tool calling in LangGraph
- Create `tools_node` for executing tool calls
- Update system prompt with tool usage guidance

**Updated System Prompt Addition:**
```
## Available Tools

You have access to these tools:

1. **get_jira_data()**: Retrieves metadata for ALL features
   - Use this first when user asks about a feature
   - Returns: feature_id, jira_key, summary, status for all features
   - You'll need the feature_id for subsequent analysis

## Workflow

When asked "Is [feature name] ready for its next phase?":
1. Call get_jira_data() to find all features
2. Identify which feature matches the user's query
3. Extract the feature_id for that feature
4. (More tools will be available in later steps)
```

**LangGraph Tool Integration Pattern:**
```python
from langgraph.prebuilt import ToolNode

# Bind tools to model
llm_with_tools = llm.bind_tools([get_jira_data])

# Add tools node to graph
workflow.add_node("tools", ToolNode([get_jira_data]))

# Add conditional edge: if agent calls tool → go to tools node
def should_continue(state):
    messages = state["messages"]
    last_message = messages[-1]
    if last_message.tool_calls:
        return "tools"
    return END

workflow.add_conditional_edges("agent", should_continue, {
    "tools": "tools",
    END: END
})
workflow.add_edge("tools", "agent")  # After tools, go back to agent
```

**Acceptance Criteria:**
- ✅ Tools successfully bound to ChatAnthropic model
- ✅ LangGraph routes tool calls to tools_node correctly
- ✅ Agent can call get_jira_data tool successfully
- ✅ Agent uses tool results to identify features
- ✅ Agent extracts feature_id from results
- ✅ Integration tests verify tool calling

---

#### 2.4 Conversation Persistence
**Files:** `cli.py` (enhanced)

**Implementation:**
- LangGraph maintains conversation state automatically via AgentState
- Messages accumulate in state using `add_messages` reducer
- CLI maintains state dict across turns in same session

**Note:** LangGraph's state management with `add_messages` automatically accumulates conversation history. The CLI just needs to pass the same state dict to graph.invoke() for each turn.

**Acceptance Criteria:**
- ✅ Agent remembers previous messages in same session
- ✅ Agent can reference earlier conversation context

---

#### 2.5 Step 2 Validation

**Manual Testing:**
```bash
You: Is the maintenance scheduling feature ready for its next phase?
Expected:
- Agent calls get_jira_data()
- Agent identifies the feature from results
- Agent mentions it found feature but needs more data (no analysis tool yet)

You: What features do you know about?
Expected:
- Agent calls get_jira_data()
- Agent lists all 4 features with summaries
```

**Automated Testing:**
```bash
pytest src/ tests/ -v
```

**Success Criteria:**
- ✅ Agent successfully retrieves JIRA data
- ✅ Agent identifies correct feature from natural language query
- ✅ Agent handles ambiguous feature names (asks for clarification)
- ✅ All tests pass, no warnings

---

### **Step 3: Testing Metrics Results Tool**

**Goal:** Agent analyzes test metrics and makes readiness decisions

**Tasks:**

#### 3.1 Understand Analysis Data Structure
**Action:** Explore `incoming_data/feature*/` to understand analysis files

**Available Analysis Types in incoming_data:**
```
metrics/
  - performance_benchmarks.json
  - pipeline_results.json
  - security_scan_results.json
  - test_coverage_report.json
  - unit_test_results.json
reviews/
  - security.json
  - stakeholders.json
  - uat.json
```

**IMPORTANT - Scope for This Module:**
For this module, we are ONLY implementing support for:
- `metrics/unit_test_results`
- `metrics/test_coverage_report`

Other analysis types (security reviews, stakeholder reviews, performance benchmarks, etc.) will be added in future modules. This keeps the initial implementation focused on test-driven decisions.

**Key Decision:** Analysis tool should accept `feature_id` and `analysis_type` parameters, but only support the two testing-related types for now

---

#### 3.2 Implement Analysis Tool
**Files:** `src/tools/analysis.py`, `src/tools/analysis_test.py`

**Implementation:**
```python
from langchain_core.tools import tool
from typing import Dict, Any
import json
from pathlib import Path

@tool
def get_analysis(feature_id: str, analysis_type: str) -> Dict[str, Any]:
    """Retrieves analysis data for a specific feature.

    Args:
        feature_id: The feature ID (e.g., 'FEAT-MS-001')
        analysis_type: Type of analysis, one of:
            - 'metrics/unit_test_results'
            - 'metrics/test_coverage_report'

    Returns:
        Analysis data from the specified file.

    Use this to assess feature quality and readiness:
    - Check unit test results for failures
    - Review test coverage
    """
    # Map feature_id → folder using utility
    # Read incoming_data/feature{N}/{analysis_type}.json
    # Return parsed JSON
    pass
```

**Error Handling:**
- Invalid feature_id → return error message
- Invalid analysis_type → return list of valid types
- Missing file → return note that analysis type not available for this feature
- Malformed JSON → return error with details

**Acceptance Criteria:**
- ✅ Tool retrieves both of the testing analysis types correctly
- ✅ Handles invalid inputs gracefully
- ✅ Unit tests verify error cases

---

#### 3.3 Integrate Analysis Tool & Update Prompt
**Files:** `src/agent/graph.py`, `src/agent/prompts.py`

**Updated System Prompt Addition:**
```
2. **get_analysis(feature_id, analysis_type)**: Retrieves specific analysis data
   - Requires feature_id from get_jira_data()
   - Analysis types available in this version:
     * 'metrics/unit_test_results' - Check for test failures
     * 'metrics/test_coverage_report' - Review test coverage
   - Call both analysis types to make comprehensive decisions

## Decision Criteria

When determining if a feature is ready for its next phase:

**Critical Rule: ANY failing tests = NOT READY**

For Development → UAT:
- ✅ All unit tests must pass (0 failures)
- ✅ Code review completed
- ✅ Security review shows LOW or MEDIUM risk (HIGH = blocker)

For UAT → Production:
- ✅ All unit tests must pass (0 failures)
- ✅ UAT testing completed with no critical issues
- ✅ Security review shows LOW risk only
- ✅ Stakeholder approvals obtained

**Always provide specific reasoning:**
- Cite exact test failure counts
- Reference specific blockers from analysis data
- Explain which criteria are met/not met
```

**Acceptance Criteria:**
- ✅ Agent can call get_analysis with correct parameters
- ✅ Agent calls multiple analysis types for comprehensive assessment
- ✅ Agent makes decisions based on test results
- ✅ Integration tests verify decision logic

---

#### 3.4 Implement Decision Logic
**Note:** Decision logic lives in the system prompt, not in code. The agent (Claude) makes decisions based on prompt instructions.

**Verification approach:**
- Provide clear decision criteria in system prompt
- Test with features that have different scenarios:
  - All tests passing → READY
  - Some tests failing → NOT READY
  - Missing data → Ask for more information

---

#### 3.5 Step 3 Validation

**Manual Testing:**

Test Case 1: Feature with failing tests
```bash
You: Is the QR code check-in feature ready for its next phase?
Expected:
- Agent calls get_jira_data()
- Agent identifies feature
- Agent calls get_analysis for unit tests
- Agent sees failures → recommends NOT READY
- Agent provides specific failure details
```

Test Case 2: Feature with all tests passing
```bash
You: Is the maintenance scheduling feature ready for its next phase?
Expected:
- Agent calls get_jira_data()
- Agent identifies feature
- Agent calls multiple analysis types
- Agent sees all tests passing → recommends READY
```

Test Case 3: Ambiguous feature name
```bash
You: Is the reservation system ready?
Expected:
- Agent calls get_jira_data()
- Agent finds multiple possible matches or no confident match
- Agent asks user for clarification
```

**Automated Testing:**
```bash
pytest src/ tests/ -v

# Verify integration tests covering:
# - Feature identification accuracy
# - Tool call sequence correctness
# - Decision logic for READY cases
# - Decision logic for NOT READY cases
```

**Success Criteria:**
- ✅ All acceptance criteria from DESIGN.md are met
- ✅ Agent correctly identifies features from natural language
- ✅ Agent makes appropriate readiness decisions based on test results
- ✅ Agent provides clear reasoning with specific evidence
- ✅ Agent handles missing/ambiguous data gracefully
- ✅ All tests pass with no warnings

---

### **Step 4: Observability Tracing**

**Goal:** Add comprehensive OpenTelemetry tracing for all agent operations

**Tasks:**

#### 4.1 OpenTelemetry Setup
**Files:** `src/observability/tracer.py`, `src/observability/tracer_test.py`

**Implementation:**
- Initialize OpenTelemetry tracer
- Create trace provider with JSON file exporter
- Configure span processor
- Set up trace context propagation

**Dependencies:**
```bash
uv add opentelemetry-api opentelemetry-sdk
```

**Configuration:**
```python
# Traces saved to: traces/trace_{timestamp}.json
# Human-readable JSON format
# Includes all spans, attributes, and timing
```

**Acceptance Criteria:**
- ✅ OpenTelemetry initialized correctly
- ✅ Trace files created in traces/ directory
- ✅ JSON format is human-readable
- ✅ Unit tests verify tracer setup

---

#### 4.2 LangChain/LangGraph Callbacks for Tracing
**Files:** `src/observability/callbacks.py`

**Implementation:**
- Create LangChain callback handler for OpenTelemetry (works with LangGraph)
- Capture spans for:
  - Graph invocations (entry/exit)
  - Node executions (agent node, tools node)
  - LLM calls (model, tokens, latency)
  - Tool calls (tool name, inputs, outputs, duration)
  - State transitions
  - Errors and exceptions

**Span Attributes to Capture:**
```python
# Agent spans
- conversation_id
- user_message
- agent_response
- tools_called (list)
- decision (ready/not_ready/needs_info)

# LLM spans
- model_name
- temperature
- prompt_tokens
- completion_tokens
- total_tokens
- latency_ms

# Tool spans
- tool_name
- tool_inputs
- tool_outputs (truncated if large)
- success (boolean)
- error_message (if failed)
```

**Acceptance Criteria:**
- ✅ Every conversation generates complete trace
- ✅ LLM calls tracked with token counts
- ✅ Tool calls tracked with inputs/outputs
- ✅ Timing data captured for all operations
- ✅ Errors captured in spans

---

#### 4.3 JSON Trace Exporter
**Files:** `src/observability/exporter.py`

**Implementation:**
- Custom exporter to write traces as JSON files
- One file per conversation
- Format: `traces/trace_{conversation_id}_{timestamp}.json`

**JSON Structure:**
```json
{
  "trace_id": "abc123...",
  "conversation_id": "conv_456",
  "timestamp": "2025-11-10T12:34:56Z",
  "spans": [
    {
      "span_id": "span_1",
      "parent_span_id": null,
      "name": "agent.investigate_feature",
      "start_time": "2025-11-10T12:34:56.100Z",
      "end_time": "2025-11-10T12:34:58.441Z",
      "duration_ms": 2341,
      "attributes": {
        "user_message": "Is QR check-in ready?",
        "agent_response": "❌ NOT READY...",
        "decision": "not_ready"
      },
      "events": [],
      "status": "OK"
    }
  ]
}
```

**Acceptance Criteria:**
- ✅ Traces saved as JSON files
- ✅ One file per conversation
- ✅ Files are human-readable
- ✅ Can correlate spans via parent_span_id

---

#### 4.4 Integrate Tracing into Agent
**Files:** `src/agent/graph.py`, `cli.py`

**Implementation:**
- Initialize tracer on application startup
- Attach LangChain callback to LangGraph via config parameter
- Generate conversation_id for each CLI session
- Ensure traces flush on exit

**LangGraph Callback Integration:**
```python
# Pass callbacks via config when invoking graph
result = graph.invoke(
    state,
    config={"callbacks": [otel_callback_handler]}
)
```

**Acceptance Criteria:**
- ✅ Traces generated for every conversation
- ✅ All agent operations captured
- ✅ Trace files written to traces/ directory

---

#### 4.5 Step 4 Validation

**Manual Testing:**
```bash
# Run a test conversation
You: Is the maintenance scheduling feature ready?
Agent: [provides answer]

# Check trace file created
ls traces/
# Should see: trace_{conversation_id}_{timestamp}.json

# Verify trace contents
cat traces/trace_*.json | jq
# Should see complete trace with all spans
```

**Automated Testing:**
```bash
pytest src/ tests/ -v

# Integration test should verify:
# - Trace file created
# - Contains expected spans
# - Timing data present
# - Tool calls captured
```

**Success Criteria:**
- ✅ Every conversation generates a trace file
- ✅ Traces include all operations (LLM calls, tool calls)
- ✅ Timing and token data captured
- ✅ Traces are human-readable JSON
- ✅ Can correlate conversation flow with trace spans

---

### **Step 5: Retry with Exponential Back-off**

**Goal:** Configure retry mechanisms for tool and LLM failures using LangChain's built-in capabilities

**Important Context:**
LangChain v1.0+ includes built-in retry logic via the `Runnable.with_retry()` method and `RunnableRetry` class. Instead of implementing retry logic from scratch, we leverage LangChain's native retry capabilities which:
- Use the battle-tested `tenacity` library under the hood
- Support exponential backoff with jitter
- Integrate seamlessly with LangChain's observability/tracing
- Work consistently across all Runnables (tools, chains, LLMs)

**Tasks:**

#### 5.1 Understanding LangChain's Retry Mechanism
**Files:** Review existing LangChain patterns

**Key Concepts:**
```python
# LangChain provides .with_retry() on all Runnables
from langchain_core.runnables import RunnableLambda

# Example: Add retry to any Runnable
retryable_runnable = some_runnable.with_retry(
    retry_if_exception_type=(ValueError, FileNotFoundError),  # Specific exceptions
    wait_exponential_jitter=True,  # Enable jitter for better backoff
    stop_after_attempt=3,  # Max attempts
)

# Under the hood, this uses tenacity's retry logic with:
# - wait_exponential_jitter() for backoff timing
# - retry_if_exception_type() for selective retries
# - stop_after_attempt() for limits
```

**When to Apply Retries:**
1. **LLM calls**: Network errors, rate limits (5xx, 429 errors)
2. **Tool execution**: File I/O errors, transient resource issues
3. **NOT for**: Logic errors, validation errors, or permanent failures

**Acceptance Criteria:**
- ✅ Understand LangChain's `with_retry()` method
- ✅ Know when to apply retries vs. when not to
- ✅ Familiar with `tenacity` exception types

---

#### 5.2 Configure Retry for LLM Calls
**Files:** `src/agent/graph.py`, `src/utils/config.py`

**Implementation:**
```python
# In src/agent/graph.py
from langchain_anthropic import ChatAnthropic

def create_agent_graph(config):
    # Create LLM with retry configuration
    llm = ChatAnthropic(
        model=config.MODEL_NAME,
        temperature=config.TEMPERATURE,
        max_tokens=config.MAX_TOKENS,
    ).with_retry(
        retry_if_exception_type=(
            # Retry on network/API errors, not on validation errors
            ConnectionError,
            TimeoutError,
        ),
        wait_exponential_jitter=True,  # Exponential backoff with jitter
        stop_after_attempt=3,  # Max 3 attempts
    )
    
    # Rest of graph setup...
```

**Configuration Options:**
Add to `src/utils/config.py`:
```python
class Settings(BaseSettings):
    # ... existing config ...
    
    # Retry configuration
    LLM_MAX_RETRY_ATTEMPTS: int = 3
    LLM_RETRY_EXPONENTIAL_JITTER: bool = True
```

**Acceptance Criteria:**
- ✅ LLM calls configured with retry logic
- ✅ Retry only on transient errors (network, timeout)
- ✅ Retry configuration is externalized to config
- ✅ Unit tests verify retry configuration

---

#### 5.3 Configure Retry for Tool Execution
**Files:** `src/tools/jira.py`, `src/tools/analysis.py`

**Implementation:**

**Option A: Wrap individual tool functions**
```python
from langchain_core.tools import tool
from langchain_core.runnables import RunnableLambda

def _read_jira_files() -> List[Dict]:
    """Internal function that does the actual file reading."""
    # File reading logic here
    pass

@tool
def get_jira_data() -> List[Dict]:
    """Retrieves metadata for ALL features from JIRA.
    
    This tool includes automatic retry logic for transient file I/O errors.
    """
    # Wrap the file reading in a retryable Runnable
    retryable_reader = RunnableLambda(_read_jira_files).with_retry(
        retry_if_exception_type=(FileNotFoundError, PermissionError, OSError),
        wait_exponential_jitter=True,
        stop_after_attempt=3,
    )
    
    try:
        return retryable_reader.invoke({})
    except Exception as e:
        # Graceful degradation after retry exhaustion
        return {
            "error": f"Failed to retrieve JIRA data after 3 retries: {str(e)}",
            "suggestion": "Check file permissions and paths"
        }
```

**Option B: Use LangGraph's node-level retry** (if needed)
LangGraph allows retry configuration at the node level during graph construction. This is useful for retrying entire node executions:
```python
# When adding nodes, you can configure retry at the node level
# This retries the entire node execution, not just a single operation
workflow.add_node(
    "tools",
    ToolNode([get_jira_data, get_analysis]).with_retry(
        retry_if_exception_type=(ConnectionError, TimeoutError),
        stop_after_attempt=2,
    )
)
```

**Recommended Approach:**
- Start with **Option A** (tool-level retries) for fine-grained control
- Consider Option B only if you need to retry entire node executions
- Keep retry scope as narrow as possible

**Acceptance Criteria:**
- ✅ Tools configured with appropriate retry logic
- ✅ Retry only on transient I/O errors
- ✅ Graceful error messages after retry exhaustion
- ✅ Unit tests verify retry behavior with mocked failures

---

#### 5.4 Observability for Retries
**Files:** `src/observability/callbacks.py`, tests

**Implementation:**

LangChain's retry mechanism automatically integrates with LangSmith/OpenTelemetry tracing. Retry attempts appear as:
- Separate spans for each retry attempt
- Parent span shows total duration including retries
- Exception information captured in span attributes

**Additional logging:**
```python
import logging

# In src/tools/jira.py or src/tools/analysis.py
logger = logging.getLogger(__name__)

def _read_jira_files() -> List[Dict]:
    """Internal function with explicit retry logging."""
    try:
        # File reading logic
        result = do_file_read()
        return result
    except (FileNotFoundError, PermissionError, OSError) as e:
        # This will be caught by retry logic, but we can log it
        logger.warning(f"File read failed, will retry: {e}")
        raise  # Re-raise to trigger retry
```

**Validation approach:**
```python
# In src/tools/jira_test.py
def test_jira_retry_on_file_error(tmp_path, monkeypatch):
    """Test that JIRA tool retries on transient errors."""
    call_count = 0
    
    def mock_read():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise FileNotFoundError("Temporary error")
        return [{"feature_id": "test"}]
    
    # Patch the internal read function
    monkeypatch.setattr("src.tools.jira._read_jira_files", mock_read)
    
    # Call tool - should succeed after retries
    result = get_jira_data()
    assert call_count == 3  # Verify retries happened
    assert result[0]["feature_id"] == "test"
```

**Acceptance Criteria:**
- ✅ Retry attempts visible in OpenTelemetry traces
- ✅ Logs show retry attempts with context
- ✅ Tests verify retry behavior using mocks
- ✅ Can diagnose transient vs. permanent failures from traces

---

#### 5.5 Step 5 Validation

**Manual Testing:**
```bash
# Test 1: Simulate transient failure with file operation
# (Requires a test mode or mock that introduces delays)

# Test 2: Review traces to confirm retry behavior
# - Check traces/ directory for retry spans
# - Verify exponential backoff timing
# - Confirm proper exception handling

# Test 3: Verify LLM retry (harder to test manually)
# - Would need to simulate API errors
# - Better tested via unit tests with mocks
```

**Automated Testing:**
```bash
pytest src/tools/jira_test.py -v -k retry
pytest src/tools/analysis_test.py -v -k retry
pytest src/agent/graph_test.py -v -k retry

# Tests should verify:
# - Retry logic triggers on transient failures
# - Exponential backoff applied (check timing)
# - Graceful failure after max attempts
# - Permanent errors don't trigger retries
```

**Success Criteria:**
- ✅ LLM calls retry on network/API errors (3 attempts max)
- ✅ Tools retry on transient I/O errors (3 attempts max)
- ✅ Exponential backoff with jitter applied
- ✅ Retry attempts visible in traces/logs
- ✅ Graceful error messages after retry exhaustion
- ✅ Permanent errors (validation, logic) don't trigger retries
- ✅ All tests pass

**Key Takeaway:**  
By using LangChain's built-in `with_retry()`, we avoid implementing custom retry logic while gaining battle-tested retry behavior, proper observability integration, and consistent patterns across the codebase.

---

### **Step 6: Evaluation with LangSmith**

**Goal:** Leverage LangSmith's built-in evaluation platform to assess agent performance

**Philosophy:** LangSmith handles evaluation *infrastructure* (dataset storage, experiment runner, metrics aggregation, comparison views). You focus on evaluation *logic* (test scenarios, custom evaluators, success criteria).

**Key Concepts:**
- **Datasets**: Collections of test inputs/outputs stored in LangSmith
- **Experiments**: Results of running your agent on a dataset (tracked automatically)
- **Evaluators**: Functions that score agent outputs (you write custom ones)
- **Comparison Views**: LangSmith UI for analyzing experiments and detecting regressions

**Dependencies:**
```bash
uv add langsmith
```

**Tasks:**

---

#### 6.1 Understanding LangSmith's Evaluation Model
**Goal:** Learn how LangSmith's evaluation system works before implementing

**Learning Objectives:**
- Understand LangSmith's dataset, experiment, and evaluator concepts
- Learn the `evaluate()` SDK function signature and usage
- Understand how to define custom evaluators
- Know how to view and analyze results in LangSmith UI

**Key Pattern:**
```python
from langsmith import Client
from langsmith.evaluation import evaluate

# LangSmith provides:
# - Dataset storage and versioning
# - Experiment runner (evaluate() function)
# - Trace collection and storage
# - Metrics aggregation and analysis
# - Comparison views in UI

# You provide:
# - Your agent/application to test
# - Custom evaluators for domain-specific scoring
# - Test scenarios as dataset examples
```

**Resources to Review:**
- LangSmith Evaluation Concepts documentation
- `evaluate()` function reference ([Python SDK](https://docs.smith.langchain.com/reference/python/evaluation))
- Example evaluation notebooks

**Acceptance Criteria:**
- ✅ Understand how to create datasets in LangSmith
- ✅ Understand `evaluate()` function signature
- ✅ Understand evaluator input/output format (Run, Example → dict)
- ✅ Know how to view experiments in LangSmith UI

---

#### 6.2 Define Test Scenarios & Create Dataset
**Files:** `src/evaluation/scenarios.py`, `tests/fixtures/evaluation_data.py`

**Goal:** Create a LangSmith dataset with diverse test scenarios

**Implementation:**
```python
# src/evaluation/scenarios.py
from langsmith import Client
from typing import List, Dict

def create_evaluation_dataset() -> str:
    """Creates or updates the evaluation dataset in LangSmith.
    
    Returns:
        Dataset name for use in evaluations
    """
    client = Client()
    
    # Define test scenarios as examples
    examples = [
        {
            "inputs": {"user_query": "Is the maintenance scheduling feature ready for UAT?"},
            "outputs": {
                "expected_decision": "ready",
                "expected_feature": "FEAT-MS-001",
                "should_call_tools": ["get_jira_data", "get_analysis"]
            },
            "metadata": {"category": "happy_path", "difficulty": "easy"}
        },
        {
            "inputs": {"user_query": "Is the QR code check-in feature ready for production?"},
            "outputs": {
                "expected_decision": "not_ready",
                "expected_feature": "FEAT-QR-002",
                "should_cite_failures": True
            },
            "metadata": {"category": "failing_tests", "difficulty": "medium"}
        },
        # ... 8+ more scenarios
    ]
    
    dataset_name = "investigator-agent-eval"
    
    # Create or update dataset
    dataset = client.create_dataset(
        dataset_name=dataset_name,
        description="Evaluation dataset for Investigator Agent - testing tool usage"
    )
    
    # Add examples to dataset
    client.create_examples(
        inputs=[ex["inputs"] for ex in examples],
        outputs=[ex["outputs"] for ex in examples],
        metadata=[ex["metadata"] for ex in examples],
        dataset_id=dataset.id
    )
    
    return dataset_name
```

**Scenario Categories (minimum 8 examples):**
1. **Happy Path**: Clear feature names, complete data, obvious decisions
   - Feature with all tests passing → READY decision
   - Feature with failing tests → NOT READY decision
2. **Ambiguous Queries**: Partial names, multiple possible matches
   - Unclear feature reference → clarification request
3. **Edge Cases**: Missing data, unexpected states
   - Missing test data → appropriate handling
   - Invalid feature name → helpful error message
4. **Tool Usage**: Verify correct tool calling patterns
   - Should call both get_jira_data and get_analysis
   - Should use correct feature_id parameter

**Important Note:** 
We are only using TWO analysis types in this module:
- `metrics/unit_test_results`
- `metrics/test_coverage_report`

Other analysis types (security reviews, stakeholder reviews, etc.) will be added in future modules.

**Acceptance Criteria:**
- ✅ At least 8 diverse test scenarios defined
- ✅ Dataset created in LangSmith via SDK
- ✅ Each example has inputs, expected outputs, and metadata
- ✅ Covers all acceptance criteria from DESIGN.md
- ✅ Scenarios focus on unit test and coverage analysis only

---

#### 6.3 Implement Custom Evaluators
**Files:** `src/evaluation/evaluators.py`, `src/evaluation/evaluators_test.py`

**Goal:** Write evaluator functions to score agent performance

**Implementation:**
```python
# src/evaluation/evaluators.py
from langsmith.schemas import Run, Example

def evaluate_feature_identification(run: Run, example: Example) -> dict:
    """Evaluates if the agent correctly identified the feature.
    
    Args:
        run: The actual agent run (contains outputs and trace)
        example: The test example (contains expected outputs)
    
    Returns:
        Evaluation result with score and reasoning
    """
    expected_feature = example.outputs.get("expected_feature")
    
    # Extract feature from agent's tool calls or response
    actual_feature = _extract_feature_from_run(run)
    
    correct = actual_feature == expected_feature
    
    return {
        "key": "feature_identification_accuracy",
        "score": 1.0 if correct else 0.0,
        "comment": f"Expected {expected_feature}, got {actual_feature}"
    }


def evaluate_tool_usage(run: Run, example: Example) -> dict:
    """Evaluates if the agent called the correct tools.
    
    Checks:
    - Did agent call get_jira_data?
    - Did agent call get_analysis with correct feature_id?
    - Did agent retrieve unit test results?
    - Did agent retrieve test coverage?
    """
    expected_tools = example.outputs.get("should_call_tools", [])
    
    # Extract tool calls from run's child runs
    actual_tools = [
        child.name for child in run.child_runs 
        if child.run_type == "tool"
    ]
    
    # Check if all expected tools were called
    missing_tools = set(expected_tools) - set(actual_tools)
    
    # Check if get_analysis was called for unit tests and coverage
    analysis_calls = [
        child for child in run.child_runs 
        if child.name == "get_analysis"
    ]
    
    called_unit_tests = any(
        "unit_test" in str(call.inputs) 
        for call in analysis_calls
    )
    called_coverage = any(
        "coverage" in str(call.inputs) 
        for call in analysis_calls
    )
    
    score = 0.0
    if not missing_tools:
        score += 0.4
    if called_unit_tests:
        score += 0.3
    if called_coverage:
        score += 0.3
    
    return {
        "key": "tool_usage_correctness",
        "score": score,
        "comment": f"Missing tools: {missing_tools}, Unit tests: {called_unit_tests}, Coverage: {called_coverage}"
    }


def evaluate_decision_quality(run: Run, example: Example) -> dict:
    """Evaluates if the agent made the correct readiness decision.
    
    Checks:
    - Correct decision (ready/not ready/needs info)
    - Cites specific test results (e.g., "3 tests failing")
    - References test metrics from analysis data
    """
    expected_decision = example.outputs.get("expected_decision")
    
    # Parse agent's final response
    agent_response = run.outputs.get("output", "")
    actual_decision = _parse_decision_from_response(agent_response)
    
    correct_decision = actual_decision == expected_decision
    
    # Check if agent cited specific evidence
    should_cite_failures = example.outputs.get("should_cite_failures", False)
    cites_test_counts = any(
        word in agent_response.lower() 
        for word in ["test", "failure", "failing", "passed"]
    ) and any(char.isdigit() for char in agent_response)
    
    # Score: 1.0 if correct decision + proper evidence, 0.5 if only correct decision
    if correct_decision:
        if should_cite_failures and cites_test_counts:
            score = 1.0
        elif not should_cite_failures:
            score = 1.0
        else:
            score = 0.5
    else:
        score = 0.0
    
    return {
        "key": "decision_quality",
        "score": score,
        "comment": f"Decision: {actual_decision} (expected: {expected_decision}), Cites evidence: {cites_test_counts}"
    }


# Helper functions
def _extract_feature_from_run(run: Run) -> str | None:
    """Extracts the feature_id the agent identified."""
    # Look through tool calls for get_analysis calls
    for child in run.child_runs:
        if child.name == "get_analysis" and child.inputs:
            return child.inputs.get("feature_id")
    return None


def _parse_decision_from_response(response: str) -> str:
    """Parses the agent's decision from its response."""
    response_lower = response.lower()
    if "not ready" in response_lower or "❌" in response:
        return "not_ready"
    elif "ready" in response_lower or "✅" in response:
        return "ready"
    elif "need" in response_lower or "more information" in response_lower:
        return "needs_info"
    return "unknown"
```

**Evaluator Dimensions:**
1. **Feature Identification Accuracy**: Did agent identify the correct feature?
2. **Tool Usage Correctness**: Did agent call the right tools with right parameters?
3. **Decision Quality**: Did agent make the correct readiness decision with evidence?

**Note:** We removed "Reasoning Quality" evaluator as it's not critical at this stage. Focus on correctness of decisions and tool usage. More sophisticated reasoning evaluation will come in future modules.

**Acceptance Criteria:**
- ✅ Three evaluators implemented (feature identification, tool usage, decision quality)
- ✅ Each evaluator returns proper format: `{"key": str, "score": float, "comment": str}`
- ✅ Evaluators focus on unit test and coverage analysis only
- ✅ Unit tests verify evaluator logic with mock Run and Example objects
- ✅ Evaluators are deterministic and testable

---

#### 6.4 Run Evaluations with LangSmith SDK
**Files:** `src/evaluation/runner.py`, `src/evaluation/runner_test.py`

**Goal:** Use LangSmith's `evaluate()` function to run experiments

**Implementation:**
```python
# src/evaluation/runner.py
from langsmith.evaluation import evaluate
from langsmith import Client
from src.agent.graph import create_agent_graph
from src.utils.config import load_config
from src.evaluation.evaluators import (
    evaluate_feature_identification,
    evaluate_tool_usage,
    evaluate_decision_quality,
)

def run_evaluation(
    dataset_name: str = "investigator-agent-eval",
    experiment_prefix: str = "investigator-eval"
) -> dict:
    """Runs evaluation using LangSmith's evaluate() function.
    
    Args:
        dataset_name: Name of the LangSmith dataset
        experiment_prefix: Prefix for the experiment name
    
    Returns:
        Experiment results from LangSmith
    """
    config = load_config()
    agent = create_agent_graph(config)
    
    # Define the target function (what to test)
    def run_agent(inputs: dict) -> dict:
        """Wrapper to run agent on a single example."""
        user_query = inputs["user_query"]
        result = agent.invoke(
            {"messages": [{"role": "user", "content": user_query}]}
        )
        return {
            "output": result["messages"][-1].content
        }
    
    # Run evaluation
    results = evaluate(
        run_agent,  # Your agent to test
        data=dataset_name,  # Dataset in LangSmith
        evaluators=[  # Your custom evaluators
            evaluate_feature_identification,
            evaluate_tool_usage,
            evaluate_decision_quality,
        ],
        experiment_prefix=experiment_prefix,
        max_concurrency=2,  # Run 2 examples in parallel
        description="Evaluating Investigator Agent on test scenarios"
    )
    
    return results


def print_evaluation_summary(results: dict):
    """Prints a summary of evaluation results.
    
    Note: Full analysis should be done in LangSmith UI.
    This is just a quick summary for the CLI.
    """
    print("\n" + "="*60)
    print("EVALUATION SUMMARY")
    print("="*60)
    
    if "experiment_url" in results:
        print(f"\n📊 View full results: {results['experiment_url']}")
    
    print("\nTo analyze results:")
    print("1. Open the URL above in your browser")
    print("2. Review aggregate metrics and pass rates")
    print("3. Drill into failing examples to view traces")
    print("4. Compare to previous experiments")
    print("\n" + "="*60 + "\n")
```

**Key Points:**
- **LangSmith handles**: Running experiments, storing results, aggregating metrics, trace collection
- **You provide**: Your agent function, your evaluators, your dataset
- **Analysis happens**: In LangSmith's web UI (comparison views, charts, trace debugging)
- **No custom report generation needed**: LangSmith provides rich UI for analysis

**Acceptance Criteria:**
- ✅ `evaluate()` runs successfully on dataset
- ✅ Results appear in LangSmith UI with experiment URL
- ✅ All three evaluators execute on all examples
- ✅ Can view detailed traces for each example in UI
- ✅ Concurrency setting works correctly

---

#### 6.5 CLI Integration & Validation
**Files:** `cli.py` (add eval mode)

**Goal:** Add CLI commands for running evaluations

**Implementation:**
```python
# cli.py (add to existing file)
import argparse
from src.evaluation.scenarios import create_evaluation_dataset
from src.evaluation.runner import run_evaluation, print_evaluation_summary

def main():
    parser = argparse.ArgumentParser(description="Investigator Agent CLI")
    parser.add_argument("--eval", action="store_true", help="Run evaluation mode")
    parser.add_argument(
        "--create-dataset", 
        action="store_true", 
        help="Create/update evaluation dataset in LangSmith"
    )
    args = parser.parse_args()
    
    if args.create_dataset:
        print("📝 Creating evaluation dataset in LangSmith...")
        dataset_name = create_evaluation_dataset()
        print(f"✅ Created dataset: {dataset_name}")
        print(f"   View at: https://smith.langchain.com/")
        return
    
    if args.eval:
        print("🚀 Running evaluation...")
        results = run_evaluation()
        print_evaluation_summary(results)
        return
    
    # ... existing CLI conversation mode ...
```

**Usage:**
```bash
# First time: Create the dataset
python cli.py --create-dataset

# Run evaluation
python cli.py --eval

# View results in LangSmith UI (URL printed by CLI)

# Normal conversation mode
python cli.py
```

**Manual Testing:**
```bash
# Test 1: Create dataset
python cli.py --create-dataset
# Verify: Dataset appears in LangSmith UI with 8+ examples

# Test 2: Run evaluation
python cli.py --eval
# Verify: 
# - Evaluation completes without errors
# - URL printed to console
# - Opening URL shows experiment results

# Test 3: View results in LangSmith UI
# Open the experiment URL and verify:
# - All examples executed
# - All three evaluators ran
# - Aggregate metrics visible
# - Can drill into individual example traces
# - Pass rate is calculated correctly
```

**Automated Testing:**
```bash
pytest src/ tests/ -v

# Verify:
# - Evaluator unit tests pass
# - Can create dataset programmatically
# - Can run evaluation (mock mode for tests)
```

**Success Criteria:**
- ✅ CLI supports `--eval` and `--create-dataset` flags
- ✅ Evaluation results link to LangSmith UI
- ✅ Can view aggregate metrics in LangSmith UI
- ✅ Can drill into individual examples to see traces
- ✅ Achieves >70% pass rate on evaluation dataset
- ✅ All evaluators execute successfully
- ✅ Can compare experiments to detect regressions (via UI)

---

## Summary: Division of Labor

### ❌ DON'T Build From Scratch:
- Custom evaluation runner framework
- Custom metrics aggregation system  
- Custom experiment comparison logic
- Custom report generation
- Custom baseline management
- Experiment storage/versioning

### ✅ DO Leverage LangSmith:
- Use `Client.create_dataset()` for test data
- Use `evaluate()` function to run experiments
- Write custom evaluators as simple functions
- Use LangSmith UI for analysis and comparison
- Let LangSmith handle trace collection and storage

### What You Implement:

| **Component** | **Your Responsibility** |
|---------------|-------------------------|
| Test Scenarios | Define inputs, expected outputs, metadata |
| Custom Evaluators | Write scoring logic for your domain (3 evaluators) |
| Dataset Creation | Use SDK to populate LangSmith dataset |
| Evaluation Trigger | Call `evaluate()` from CLI |
| Analysis | Use LangSmith UI to review results |

### What LangSmith Provides:

| **Component** | **LangSmith Handles** |
|---------------|----------------------|
| Dataset Storage | Versioned storage with UI for viewing |
| Experiment Runner | `evaluate()` function with concurrency |
| Trace Collection | Automatic capture of all runs and tool calls |
| Metrics Aggregation | Automatic rollup of evaluator scores |
| Comparison Views | UI for comparing experiments and detecting regressions |
| Historical Tracking | All experiments stored for future reference |

---

## Validation Checklist (Final)

After completing all steps, verify:

### Code Quality
- [ ] All unit tests pass (`pytest src/ -v`)
- [ ] All integration tests pass (`pytest tests/ -v`)
- [ ] No deprecation warnings
- [ ] No linting errors (if using ruff/pylint)
- [ ] Type hints present and correct
- [ ] Documentation strings for all public functions

### Functionality
- [ ] Agent correctly identifies features from natural language
- [ ] Agent makes appropriate readiness decisions based on test results
- [ ] Agent handles missing/ambiguous data gracefully
- [ ] Agent provides clear reasoning with specific evidence
- [ ] Conversation history maintained correctly

### Observability
- [ ] Traces generated for every conversation
- [ ] Traces include all operations (LLM calls, tool calls, decisions)
- [ ] Trace files are human-readable JSON
- [ ] Can correlate conversation flow with trace data
- [ ] Retry attempts visible in traces

### Evaluation
- [ ] Evaluation dataset created in LangSmith with 8+ scenarios
- [ ] Three custom evaluators implemented (feature ID, tool usage, decision quality)
- [ ] Can run evaluations via CLI (`python cli.py --eval`)
- [ ] Achieves >70% pass rate on evaluation dataset
- [ ] Results viewable in LangSmith UI with experiment URL
- [ ] Can view traces for individual examples in LangSmith
- [ ] Can compare experiments to detect regressions (via LangSmith UI)

### Documentation
- [ ] README.md explains setup and usage
- [ ] .env.example documents all config variables
- [ ] Code is self-documenting with clear naming
- [ ] Comments explain "why" not "what"

---

## Common Pitfalls to Avoid

1. **Skipping validation steps:** Always verify each step works before moving on
2. **Ignoring test failures:** Never commit failing tests or suppress warnings
3. **Copy-pasting code:** Understand what you're building; ask questions
4. **Over-engineering:** Keep it simple; follow YAGNI (You Aren't Gonna Need It)
5. **Forgetting to test manually:** Automated tests are necessary but not sufficient
6. **Not checking traces:** Traces reveal what's actually happening
7. **Rushing through prompts:** System prompt quality directly impacts agent quality

---

## Next Steps After Completion

Once all steps are complete and validated:

1. **Run full evaluation suite** and ensure >70% pass rate
2. **Test with all 4 features** in incoming_data/
3. **Review traces** for any unexpected behavior
4. **Document any learnings** or challenges encountered
5. **Consider enhancements:**
   - Additional analysis types
   - More sophisticated decision logic
   - Multi-turn conversation improvements
   - Memory across sessions (optional Step 7)

---

## Success Criteria Summary

The Investigator Agent is complete when:

- ✅ Correctly identifies features from natural language descriptions
- ✅ Makes appropriate phase progression decisions based on test results
- ✅ Handles missing/ambiguous data gracefully with helpful error messages
- ✅ Provides clear reasoning for all decisions with specific evidence
- ✅ Includes comprehensive observability (OpenTelemetry traces)
- ✅ Demonstrates retry logic with exponential backoff
- ✅ Passes automated evaluation suite with >70% accuracy
- ✅ All code quality standards met (no failing tests, warnings, or linting errors)

**Remember:** Quality over speed. It's better to have working, well-tested code than to rush through and create technical debt.
