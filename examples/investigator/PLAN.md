# Investigator Agent Implementation Plan (LangChain + Python) - Module 8

## Overview

Python + LangChain v1.x implementation of the Feature Readiness Investigator Agent for Module 8. This document covers **how** to build the expanded agent with comprehensive retrieval and context management capabilities.

**Module 8 Focus**: Retrieval and context window management

## Prerequisites

This plan assumes you have completed Module 7 and have a working agent with:
- Basic LangGraph workflow
- JIRA tool
- Basic analysis tool (2 metrics types)
- OpenTelemetry tracing
- Retry logic
- LangSmith evaluation

If you don't have this starting point, use the provided `module-07-complete/` example.

## Technical Stack

**Python 3.13.9** with async/await

The latest versions of each of these packages:

- **uv** for dependency and venv management
- **LangChain v1.0.5** for core framework
- **LangGraph v1.0.2** for agent orchestration
- **langchain-anthropic** for Anthropic Claude integration
- **LangSmith** for evaluation, tracing, and observability
- **OpenTelemetry v1.38.0** for local observability and tracing (JSON export)
- **Pydantic 2.12.4** for data validation and tool schemas
- **pydantic-settings 2.11.0** for configuration management
- **pytest v9.0.0** for testing
- **python-dotenv** for .env file support

## New Dependencies for Module 8

```bash
# No new external dependencies required
# We'll use subprocess to call ripgrep (assumes ripgrep installed on system)
# LangChain's ConversationSummaryMemory is already included in langchain package
```

## Implementation Goals
- Expand data retrieval to all 8 analysis types
- Add planning document tools (list, read, search with ripgrep)
- Implement context window management using ConversationSummaryMemory
- Maintain code quality and test coverage
- Demonstrate handling of large data volumes
- Keep tool execution simple (direct file access, not vector DB)

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
The recommended order of implementation is defined in [STEPS.md](STEPS.md). This plan provides detailed implementation guidance for each step.

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
│   │   ├── memory.py            # ConversationSummaryMemory setup (NEW)
│   │   ├── graph_test.py
│   │   ├── state_test.py
│   │   ├── prompts_test.py
│   │   └── memory_test.py       # (NEW)
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── jira.py              # get_jira_data tool (FROM MODULE 7)
│   │   ├── jira_test.py
│   │   ├── analysis.py          # get_analysis tool (EXPAND IN STEP 1-2)
│   │   ├── analysis_test.py
│   │   ├── planning.py          # Planning doc tools (NEW IN STEP 3)
│   │   └── planning_test.py     # (NEW)
│   ├── observability/
│   │   ├── __init__.py
│   │   ├── tracer.py            # OpenTelemetry setup
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
│       ├── scenarios.py         # Test scenario definitions (UPDATE STEP 6)
│       ├── evaluators.py        # Custom evaluator functions (UPDATE STEP 6)
│       ├── evaluators_test.py
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
│   │   ├── jira/
│   │   ├── metrics/            # 5 files
│   │   ├── reviews/            # 3 files
│   │   └── planning/           # 7-10 large .md files
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

This guide follows the order defined in [STEPS.md](STEPS.md) and builds incrementally from your Module 7 agent.

---

### **Step 1: Add Comprehensive Metrics Analysis**

**Goal:** Expand `get_analysis` tool to support all 5 metrics types

**Current State (From Module 7):**
```python
# src/tools/analysis.py
@tool
def get_analysis(feature_id: str, analysis_type: str) -> Dict[str, Any]:
    """Supports: metrics/unit_test_results, metrics/test_coverage_report"""
```

**Target State:**
```python
@tool
def get_analysis(feature_id: str, analysis_type: str) -> Dict[str, Any]:
    """Supports all 5 metrics types:
    - metrics/unit_test_results
    - metrics/test_coverage_report  
    - metrics/pipeline_results        # NEW
    - metrics/performance_benchmarks  # NEW
    - metrics/security_scan_results   # NEW
    """
```

#### 1.1 Update Analysis Tool

**Files:** `src/tools/analysis.py`, `src/tools/analysis_test.py`

**Implementation:**
```python
# The tool already supports any analysis_type parameter
# Just update the docstring and add validation

VALID_METRICS = [
    "metrics/unit_test_results",
    "metrics/test_coverage_report",
    "metrics/pipeline_results",
    "metrics/performance_benchmarks",
    "metrics/security_scan_results"
]

@tool
def get_analysis(feature_id: str, analysis_type: str) -> Dict[str, Any]:
    """Retrieves analysis data for a specific feature.
    
    Args:
        feature_id: Feature ID (e.g., 'FEAT-MS-001')
        analysis_type: One of the supported types below
    
    Metrics types:
    - metrics/unit_test_results - Unit test execution summary
    - metrics/test_coverage_report - Code coverage statistics  
    - metrics/pipeline_results - CI/CD pipeline execution results
    - metrics/performance_benchmarks - Performance test results
    - metrics/security_scan_results - Automated security scan findings
    
    Returns:
        Dict containing analysis data from JSON file
    """
    if analysis_type not in VALID_METRICS:
        return {
            "error": f"Invalid metrics type: {analysis_type}",
            "valid_types": VALID_METRICS
        }
    
    # Rest of existing implementation...
```

**Unit Tests:**
```python
# src/tools/analysis_test.py

def test_get_analysis_pipeline_results():
    """Test pipeline results retrieval."""
    result = get_analysis("FEAT-MS-001", "metrics/pipeline_results")
    assert "build_number" in result
    assert "status" in result

def test_get_analysis_performance_benchmarks():
    """Test performance benchmarks retrieval."""
    result = get_analysis("FEAT-MS-001", "metrics/performance_benchmarks")
    assert "p95_latency" in result or "response_time" in result

def test_get_analysis_security_scan_results():
    """Test security scan retrieval."""
    result = get_analysis("FEAT-MS-001", "metrics/security_scan_results")
    assert "overall_risk_level" in result or "vulnerabilities" in result

def test_get_analysis_invalid_metrics_type():
    """Test error handling for invalid metrics type."""
    result = get_analysis("FEAT-MS-001", "metrics/invalid")
    assert "error" in result
    assert "valid_types" in result
```

#### 1.2 Update System Prompt

**Files:** `src/agent/prompts.py`

**Add to system prompt:**
```python
SYSTEM_PROMPT = """
You are the Investigator Agent for the CommunityShare platform.

[... existing role description ...]

## Available Tools

1. **get_jira_data()**: Retrieves metadata for ALL features
   [... existing description ...]

2. **get_analysis(feature_id, analysis_type)**: Retrieves analysis data

   **Metrics Types:**
   - metrics/unit_test_results - Check for test failures
   - metrics/test_coverage_report - Verify coverage meets threshold (80%+)
   - metrics/pipeline_results - Verify CI/CD pipeline success
   - metrics/security_scan_results - Check for vulnerabilities
   - metrics/performance_benchmarks - Verify performance SLAs

## Comprehensive Assessment Workflow

When assessing feature readiness, retrieve ALL relevant metrics:

**For Development → UAT:**
- ✅ metrics/unit_test_results (all passing)
- ✅ metrics/test_coverage_report (≥80%)
- ✅ metrics/pipeline_results (successful)
- ✅ metrics/security_scan_results (LOW or MEDIUM risk)

**For UAT → Production:**
- ✅ metrics/unit_test_results (all passing)
- ✅ metrics/test_coverage_report (≥80%)
- ✅ metrics/pipeline_results (successful)
- ✅ metrics/security_scan_results (LOW risk only)
- ✅ metrics/performance_benchmarks (meet SLA requirements)

**Critical Rule:** Block progression if ANY critical issues found in metrics.
"""
```

#### 1.3 Integration Testing

**Files:** `tests/integration/test_tools_integration.py`

```python
def test_comprehensive_metrics_retrieval():
    """Test retrieving all 5 metrics types for a feature."""
    feature_id = "FEAT-MS-001"
    
    metrics_types = [
        "metrics/unit_test_results",
        "metrics/test_coverage_report",
        "metrics/pipeline_results",
        "metrics/performance_benchmarks",
        "metrics/security_scan_results"
    ]
    
    for metrics_type in metrics_types:
        result = get_analysis(feature_id, metrics_type)
        assert "error" not in result, f"Failed to retrieve {metrics_type}"
        assert isinstance(result, dict)
```

**Acceptance Criteria:**
- ✅ Tool accepts all 5 metrics types
- ✅ Tool returns valid data for each type
- ✅ Tool validates analysis_type parameter
- ✅ Unit tests verify all 5 types
- ✅ Integration test verifies end-to-end retrieval
- ✅ Agent system prompt includes all 5 types
- ✅ Manual CLI test shows agent retrieving multiple metrics

**Manual Validation:**
```bash
python cli.py

You: Is the maintenance scheduling feature ready for production?

Expected behavior:
- Agent calls get_jira_data()
- Agent calls get_analysis for unit_test_results
- Agent calls get_analysis for test_coverage_report
- Agent calls get_analysis for pipeline_results
- Agent calls get_analysis for security_scan_results
- Agent calls get_analysis for performance_benchmarks
- Agent synthesizes all metrics into decision
- Agent response cites specific findings from each metric
```

---

### **Step 2: Add Review Analysis Tools**

**Goal:** Add support for 3 review types

#### 2.1 Update Analysis Tool for Reviews

**Files:** `src/tools/analysis.py`, `src/tools/analysis_test.py`

**Implementation:**
```python
VALID_METRICS = [
    # ... existing metrics ...
]

VALID_REVIEWS = [
    "reviews/security",
    "reviews/uat", 
    "reviews/stakeholders"
]

VALID_ANALYSIS_TYPES = VALID_METRICS + VALID_REVIEWS

@tool
def get_analysis(feature_id: str, analysis_type: str) -> Dict[str, Any]:
    """Retrieves analysis data for a specific feature.
    
    Args:
        feature_id: Feature ID (e.g., 'FEAT-MS-001')
        analysis_type: One of the supported types below
    
    Metrics types:
    [... existing metrics documentation ...]
    
    Review types:
    - reviews/security - Security review results, vulnerabilities, compliance
    - reviews/uat - User acceptance testing feedback and approval status
    - reviews/stakeholders - Stakeholder sign-offs and approvals
    
    Returns:
        Dict containing analysis data from JSON file
    """
    if analysis_type not in VALID_ANALYSIS_TYPES:
        return {
            "error": f"Invalid analysis type: {analysis_type}",
            "valid_types": VALID_ANALYSIS_TYPES
        }
    
    # Rest of implementation unchanged - already handles any path
```

**Unit Tests:**
```python
# src/tools/analysis_test.py

def test_get_analysis_security_review():
    """Test security review retrieval."""
    result = get_analysis("FEAT-MS-001", "reviews/security")
    assert "status" in result or "overall_risk_level" in result

def test_get_analysis_uat_review():
    """Test UAT review retrieval."""
    result = get_analysis("FEAT-QR-002", "reviews/uat")
    assert "status" in result or "feedback" in result

def test_get_analysis_stakeholders_review():
    """Test stakeholders review retrieval."""
    result = get_analysis("FEAT-MS-001", "reviews/stakeholders")
    assert "approvals" in result or "product_manager" in result
```

#### 2.2 Update System Prompt for Reviews

**Files:** `src/agent/prompts.py`

**Add to system prompt:**
```python
## Review Analysis

In addition to metrics, check review outcomes for production readiness:

**Review Types:**
- reviews/security - Security review results and risk assessment
- reviews/uat - User acceptance testing feedback
- reviews/stakeholders - Stakeholder sign-offs and approvals

**Review Decision Rules:**

For UAT → Production transitions:
- ✅ Security review must be APPROVED with LOW risk
- ✅ UAT review must be PASSED with no critical issues  
- ✅ All required stakeholder approvals must be obtained

**Blocking Conditions:**
- HIGH or CRITICAL security risk = BLOCK
- Critical issues in UAT = BLOCK
- Missing stakeholder approvals = BLOCK

When you find blocking conditions in reviews, cite specific findings:
- "Security review shows MEDIUM risk with 3 unresolved findings"
- "UAT has 2 critical issues: [list specific issues]"
- "Stakeholder approvals incomplete: Engineering Lead approval PENDING"
```

**Acceptance Criteria:**
- ✅ Tool accepts all 3 review types
- ✅ Unit tests verify all 3 review types
- ✅ System prompt includes review decision rules
- ✅ Integration test verifies review-based blocking
- ✅ Manual test shows agent citing review findings

**Manual Validation:**
```bash
python cli.py

You: Is the QR code check-in feature ready for production?

Expected behavior:
- Agent retrieves all metrics
- Agent retrieves all reviews
- Agent identifies blockers in security review
- Agent identifies issues in UAT review
- Agent makes NOT READY decision citing review findings
```

---

### **Step 3: Add Planning Document Tools**

**Goal:** Enable agent to list, read, and search planning documents

#### 3.1 Create Planning Tools Module

**Files:** `src/tools/planning.py`, `src/tools/planning_test.py`

**Implementation:**
```python
# src/tools/planning.py

from langchain_core.tools import tool
from typing import List, Dict
from pathlib import Path
import subprocess
import json

@tool
def list_planning_docs(feature_id: str) -> List[str]:
    """List all planning documents available for a feature.
    
    Args:
        feature_id: Feature ID (e.g., 'FEAT-MS-001')
    
    Returns:
        List of document names
    
    Use this to:
    - See what documentation exists
    - Determine which documents to read
    - Avoid loading unnecessary large documents
    """
    from src.utils.file_utils import get_feature_folder
    
    try:
        folder = get_feature_folder(feature_id)
        planning_path = Path("data/incoming") / folder / "planning"
        
        if not planning_path.exists():
            return {"error": f"Planning directory not found for {feature_id}"}
        
        docs = [f.name for f in planning_path.glob("*.md")]
        return sorted(docs)
    
    except Exception as e:
        return {"error": f"Failed to list planning docs: {str(e)}"}


@tool
def read_planning_doc(feature_id: str, doc_name: str) -> str:
    """Read a specific planning document.
    
    Args:
        feature_id: Feature ID (e.g., 'FEAT-MS-001')
        doc_name: Document name from list_planning_docs
    
    Returns:
        Full document content (may be large, 10-15KB)
    
    WARNING: Planning documents can be large. Consider using
    search_planning_docs if you're looking for specific information.
    """
    from src.utils.file_utils import get_feature_folder
    
    try:
        folder = get_feature_folder(feature_id)
        doc_path = Path("data/incoming") / folder / "planning" / doc_name
        
        if not doc_path.exists():
            return {"error": f"Document not found: {doc_name}"}
        
        with open(doc_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return content
    
    except Exception as e:
        return {"error": f"Failed to read document: {str(e)}"}


@tool
def search_planning_docs(feature_id: str, query: str) -> List[Dict[str, str]]:
    """Search planning documents using ripgrep.
    
    Args:
        feature_id: Feature ID (e.g., 'FEAT-MS-001')
        query: Search query (regex supported)
    
    Returns:
        List of matches with filename, line number, and matching text
    
    Use this to:
    - Find specific information across all planning docs
    - Avoid reading entire large documents
    - Locate mentions of requirements, APIs, or components
    
    Example: search_planning_docs('FEAT-MS-001', 'authentication')
    """
    from src.utils.file_utils import get_feature_folder
    
    try:
        folder = get_feature_folder(feature_id)
        planning_path = Path("data/incoming") / folder / "planning"
        
        if not planning_path.exists():
            return {"error": f"Planning directory not found for {feature_id}"}
        
        # Call ripgrep with JSON output
        result = subprocess.run(
            ["rg", "--json", query, str(planning_path)],
            capture_output=True,
            text=True
        )
        
        # Parse ripgrep JSON output
        matches = []
        for line in result.stdout.strip().split('\n'):
            if line:
                try:
                    data = json.loads(line)
                    if data.get('type') == 'match':
                        matches.append({
                            'file': Path(data['data']['path']['text']).name,
                            'line_number': data['data']['line_number'],
                            'match': data['data']['lines']['text'].strip()
                        })
                except json.JSONDecodeError:
                    continue
        
        if len(matches) == 0:
            return {"message": f"No matches found for '{query}'"}
        
        return matches[:20]  # Limit to 20 matches to avoid context overflow
    
    except FileNotFoundError:
        return {"error": "ripgrep not found - install with: brew install ripgrep"}
    except Exception as e:
        return {"error": f"Search failed: {str(e)}"}
```

**Unit Tests:**
```python
# src/tools/planning_test.py

def test_list_planning_docs():
    """Test listing planning documents."""
    result = list_planning_docs("FEAT-MS-001")
    assert isinstance(result, list)
    assert len(result) > 0
    assert "USER_STORY.md" in result or "DESIGN_DOC.md" in result

def test_read_planning_doc():
    """Test reading a planning document."""
    result = read_planning_doc("FEAT-MS-001", "USER_STORY.md")
    assert isinstance(result, str)
    assert len(result) > 100  # Should have substantial content

def test_search_planning_docs():
    """Test searching planning documents."""
    result = search_planning_docs("FEAT-MS-001", "maintenance")
    assert isinstance(result, list)
    assert len(result) > 0
    assert "file" in result[0]
    assert "match" in result[0]

def test_search_planning_docs_no_matches():
    """Test search with no matches."""
    result = search_planning_docs("FEAT-MS-001", "xyzabc123impossible")
    assert "message" in result or len(result) == 0
```

#### 3.2 Integrate Planning Tools into Agent

**Files:** `src/agent/graph.py`

**Update tool binding:**
```python
from src.tools.planning import list_planning_docs, read_planning_doc, search_planning_docs

# Bind all tools including new planning tools
llm_with_tools = llm.bind_tools([
    get_jira_data,
    get_analysis,
    list_planning_docs,      # NEW
    read_planning_doc,       # NEW
    search_planning_docs     # NEW
])

# Update tools node
tools_node = ToolNode([
    get_jira_data,
    get_analysis,
    list_planning_docs,
    read_planning_doc,
    search_planning_docs
])
```

#### 3.3 Update System Prompt

**Files:** `src/agent/prompts.py`

**Add planning doc section:**
```python
## Planning Document Tools

You have access to planning documentation for each feature:

**Available Documents (typical):**
- USER_STORY.md - User stories and acceptance criteria
- DESIGN_DOC.md - Detailed design decisions
- ARCHITECTURE.md - System architecture and components
- API_SPECIFICATION.md - API contracts and endpoints
- DATABASE_SCHEMA.md - Database schema and migrations
- DEPLOYMENT_PLAN.md - Deployment strategy
- TEST_STRATEGY.md - Testing approach

**Tool Usage Strategy:**

1. **list_planning_docs(feature_id)** - Start here to see what's available
2. **search_planning_docs(feature_id, query)** - PREFERRED for finding specific info
3. **read_planning_doc(feature_id, doc_name)** - Only when you need full context

**When to Use Planning Docs:**
- User asks about requirements or acceptance criteria
- Need to understand architectural decisions
- Clarifying expected API behavior
- Verifying deployment prerequisites

**IMPORTANT - Context Management:**
Planning documents are LARGE (10-15KB each). Reading multiple full documents
will quickly fill your context window. PREFER search_planning_docs for targeted
information retrieval. Only use read_planning_doc when you truly need full context.
```

**Acceptance Criteria:**
- ✅ All 3 planning tools implemented and tested
- ✅ Tools handle missing files gracefully
- ✅ Ripgrep integration works correctly
- ✅ Tools integrated into agent graph
- ✅ System prompt guides tool selection
- ✅ Unit tests for all 3 tools
- ✅ Integration test showing intelligent tool usage
- ✅ Manual test demonstrates search vs read preference

**Manual Validation:**
```bash
python cli.py

You: What are the acceptance criteria for the maintenance scheduling feature?

Expected:
- Agent calls list_planning_docs
- Agent sees USER_STORY.md available
- Agent calls search_planning_docs with "acceptance criteria" query
- Agent returns specific acceptance criteria WITHOUT reading full doc
- Check trace: search_planning_docs called, NOT read_planning_doc

You: Tell me everything in the design document for that feature.

Expected:
- Agent calls read_planning_doc for DESIGN_DOC.md
- Agent returns comprehensive summary of design doc
- Check trace: read_planning_doc called (appropriate for "everything" request)
```

---

### **Step 4: Implement Context Window Management**

**Goal:** Add ConversationSummaryMemory to handle large data volumes

#### 4.1 Create Memory Module

**Files:** `src/agent/memory.py`, `src/agent/memory_test.py`

**Implementation:**
```python
# src/agent/memory.py

from langchain.memory import ConversationSummaryMemory
from langchain_anthropic import ChatAnthropic
from typing import Dict

def create_conversation_memory(llm: ChatAnthropic, max_token_limit: int = 2000) -> ConversationSummaryMemory:
    """Create ConversationSummaryMemory for the agent.
    
    Args:
        llm: The language model to use for summarization
        max_token_limit: Token threshold to trigger summarization
    
    Returns:
        Configured ConversationSummaryMemory instance
    """
    memory = ConversationSummaryMemory(
        llm=llm,
        max_token_limit=max_token_limit,
        return_messages=True,
        memory_key="chat_history"
    )
    
    return memory
```

**Unit Tests:**
```python
# src/agent/memory_test.py

from langchain_anthropic import ChatAnthropic
from src.agent.memory import create_conversation_memory

def test_create_conversation_memory():
    """Test memory creation."""
    llm = ChatAnthropic(model="claude-3-5-sonnet-20241022")
    memory = create_conversation_memory(llm, max_token_limit=1000)
    
    assert memory is not None
    assert memory.max_token_limit == 1000
    assert memory.return_messages == True

def test_memory_saves_context():
    """Test that memory saves conversation context."""
    llm = ChatAnthropic(model="claude-3-5-sonnet-20241022")
    memory = create_conversation_memory(llm)
    
    # Save a conversation turn
    memory.save_context(
        {"input": "What is the capital of France?"},
        {"output": "The capital of France is Paris."}
    )
    
    # Load memory variables
    memory_vars = memory.load_memory_variables({})
    assert "history" in memory_vars
```

#### 4.2 Integrate Memory into Agent Graph

**Files:** `src/agent/graph.py`

**Update graph to use memory:**
```python
from src.agent.memory import create_conversation_memory

def create_agent_graph(config):
    """Creates agent graph with memory management."""
    
    # Initialize LLM
    llm = ChatAnthropic(
        model=config.MODEL_NAME,
        temperature=config.TEMPERATURE,
        max_tokens=config.MAX_TOKENS
    )
    
    # Initialize memory
    memory = create_conversation_memory(
        llm=llm,
        max_token_limit=config.MEMORY_MAX_TOKEN_LIMIT
    )
    
    # Bind tools
    llm_with_tools = llm.bind_tools([...])
    
    # Define agent node with memory integration
    def call_model(state: AgentState):
        messages = state["messages"]
        
        # Load memory context (includes summary if exists)
        memory_context = memory.load_memory_variables({})
        
        # If there's a summary, prepend it
        if memory_context.get("history"):
            messages = list(memory_context["history"]) + list(messages)
        
        # Call LLM
        response = llm_with_tools.invoke(messages)
        
        # Save to memory (will trigger summarization if needed)
        if len(state["messages"]) > 0:
            last_msg = state["messages"][-1]
            memory.save_context(
                {"input": last_msg.content if hasattr(last_msg, 'content') else str(last_msg)},
                {"output": response.content}
            )
        
        return {"messages": [response]}
    
    # Rest of graph setup...
```

#### 4.3 Add Memory Configuration

**Files:** `src/utils/config.py`, `.env.example`

**Update config:**
```python
# src/utils/config.py

class Settings(BaseSettings):
    # ... existing settings ...
    
    # Context management (NEW)
    MEMORY_MAX_TOKEN_LIMIT: int = 2000  # When to trigger summarization
    MEMORY_STRATEGY: str = "summary"  # Future: support other strategies
```

**Update .env.example:**
```bash
# Context Management
MEMORY_MAX_TOKEN_LIMIT=2000
MEMORY_STRATEGY=summary
```

#### 4.4 Add Memory Observability

**Files:** `src/observability/callbacks.py`

**Track memory operations:**
```python
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

def call_model(state: AgentState):
    with tracer.start_as_current_span("agent.call_model") as span:
        # ... existing code ...
        
        # Track memory operations
        memory_vars = memory.load_memory_variables({})
        if "history" in memory_vars and len(memory_vars["history"]) > 0:
            span.set_attribute("memory.summarized", True)
            span.set_attribute("memory.summary_message_count", len(memory_vars["history"]))
        else:
            span.set_attribute("memory.summarized", False)
        
        # Track estimated tokens (rough estimate)
        total_chars = sum(len(str(m)) for m in messages)
        estimated_tokens = total_chars // 4  # Rough estimate: 4 chars per token
        span.set_attribute("memory.estimated_tokens", estimated_tokens)
```

**Acceptance Criteria:**
- ✅ ConversationSummaryMemory created and configured
- ✅ Memory integrated into agent graph
- ✅ Memory configuration externalized
- ✅ Summarization triggers when threshold exceeded
- ✅ Agent maintains context across summarization
- ✅ Observability tracks memory operations
- ✅ Unit tests verify memory behavior
- ✅ Integration test with large data volumes

**Manual Validation (Context Stress Test):**
```bash
python cli.py

You: Tell me about the maintenance scheduling feature. What's in the design doc?
Agent: [Reads DESIGN_DOC.md - ~12KB added to context]

You: Now tell me about the QR code feature. Read its architecture doc.
Agent: [Reads ARCHITECTURE.md - another ~12KB]
[Memory should summarize first exchange]

You: Compare the two features.
Agent: [Can still reference earlier conversations via summary]
[Makes comparison despite large context usage]

Expected in traces:
- memory.summarized = false initially
- memory.summarized = true after second doc read
- memory.summary_message_count > 0
- Agent response references both features coherently
```

---

### **Step 5: Update Observability for New Tools**

**Goal:** Ensure tracing captures all new tool operations

#### 5.1 Add Planning Tool Spans

**Files:** `src/tools/planning.py`

**Wrap tools with tracing:**
```python
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

@tool
def list_planning_docs(feature_id: str) -> List[str]:
    """..."""
    with tracer.start_as_current_span("tool.list_planning_docs") as span:
        span.set_attribute("feature_id", feature_id)
        
        # ... existing implementation ...
        
        span.set_attribute("docs_found", len(docs))
        span.set_attribute("docs", json.dumps(docs))
        return docs

@tool
def read_planning_doc(feature_id: str, doc_name: str) -> str:
    """..."""
    with tracer.start_as_current_span("tool.read_planning_doc") as span:
        span.set_attribute("feature_id", feature_id)
        span.set_attribute("doc_name", doc_name)
        
        # ... existing implementation ...
        
        span.set_attribute("doc_size_bytes", len(content))
        span.set_attribute("doc_size_kb", len(content) / 1024)
        return content

@tool
def search_planning_docs(feature_id: str, query: str) -> List[Dict[str, str]]:
    """..."""
    with tracer.start_as_current_span("tool.search_planning_docs") as span:
        span.set_attribute("feature_id", feature_id)
        span.set_attribute("query", query)
        
        # ... existing implementation ...
        
        span.set_attribute("matches_found", len(matches))
        span.set_attribute("files_searched", len(set(m['file'] for m in matches)))
        return matches
```

#### 5.2 Enhance Conversation Span

**Files:** `src/agent/graph.py`

**Add data retrieval metrics:**
```python
with tracer.start_as_current_span("agent.conversation") as span:
    span.set_attribute("conversation_id", conversation_id)
    span.set_attribute("user_message", user_input)
    
    # Track tool calls (count by type)
    tool_calls = [c for c in state["messages"] if hasattr(c, 'tool_calls')]
    metrics_retrieved = sum(1 for c in tool_calls if "metrics/" in str(c))
    reviews_retrieved = sum(1 for c in tool_calls if "reviews/" in str(c))
    planning_lists = sum(1 for c in tool_calls if "list_planning" in str(c))
    planning_reads = sum(1 for c in tool_calls if "read_planning" in str(c))
    planning_searches = sum(1 for c in tool_calls if "search_planning" in str(c))
    
    span.set_attribute("metrics_retrieved", metrics_retrieved)
    span.set_attribute("reviews_retrieved", reviews_retrieved)
    span.set_attribute("planning_docs_listed", planning_lists)
    span.set_attribute("planning_docs_read", planning_reads)
    span.set_attribute("planning_docs_searched", planning_searches)
```

**Acceptance Criteria:**
- ✅ Planning tool operations traced with spans
- ✅ Document sizes logged
- ✅ Search results logged (match counts)
- ✅ Memory operations tracked
- ✅ Conversation spans show comprehensive stats
- ✅ Can analyze traces to understand retrieval patterns
- ✅ All spans include timing information

---

### **Step 6: Update Evaluations for Comprehensive Retrieval**

**Goal:** Adapt evaluation suite for Module 8 capabilities

#### 6.1 Create Module 8 Evaluation Scenarios

**Files:** `src/evaluation/scenarios.py`

**Update dataset creation:**
```python
def create_evaluation_dataset() -> str:
    """Creates Module 8 evaluation dataset."""
    
    examples = [
        # Scenario 1: Comprehensive retrieval
        {
            "inputs": {"user_query": "Is the maintenance scheduling feature ready for production?"},
            "outputs": {
                "expected_decision": "ready",
                "expected_feature": "FEAT-MS-001",
                "expected_metrics": [
                    "metrics/unit_test_results",
                    "metrics/test_coverage_report",
                    "metrics/pipeline_results",
                    "metrics/security_scan_results",
                    "metrics/performance_benchmarks"
                ],
                "expected_reviews": [
                    "reviews/security",
                    "reviews/uat",
                    "reviews/stakeholders"
                ],
                "should_use_planning_docs": False
            },
            "metadata": {"category": "comprehensive_retrieval", "difficulty": "medium"}
        },
        
        # Scenario 2: Large docs + context management
        {
            "inputs": {
                "user_query": "What are the acceptance criteria for QR code check-in? Then assess production readiness."
            },
            "outputs": {
                "expected_decision": "not_ready",
                "expected_feature": "FEAT-QR-002",
                "should_use_planning_docs": True,
                "involves_large_docs": True
            },
            "metadata": {"category": "context_management", "difficulty": "hard"}
        },
        
        # Scenario 3: Multi-feature comparison
        {
            "inputs": {
                "user_query": "Compare reservation system and QR code features. Which is closer to production?"
            },
            "outputs": {
                "expected_features": ["FEAT-RS-003", "FEAT-QR-002"],
                "involves_large_docs": True,
                "should_retrieve_multiple_features": True
            },
            "metadata": {"category": "context_stress", "difficulty": "hard"}
        },
        
        # Scenario 4: Tool selection (search vs read)
        {
            "inputs": {
                "user_query": "Does maintenance scheduling's architecture mention WebSocket?"
            },
            "outputs": {
                "expected_feature": "FEAT-MS-001",
                "should_use_planning_docs": True,
                "should_prefer_search": True  # Should use search, not read
            },
            "metadata": {"category": "tool_selection", "difficulty": "medium"}
        },
        
        # Add 4+ more scenarios...
    ]
    
    dataset_name = "investigator-agent-module-8"
    
    # Create in LangSmith...
```

#### 6.2 Implement New Evaluators

**Files:** `src/evaluation/evaluators.py`

**Add comprehensive retrieval evaluator:**
```python
def evaluate_comprehensive_retrieval(run: Run, example: Example) -> dict:
    """Evaluates comprehensive data retrieval."""
    # Implementation from STEPS.md Step 6...

def evaluate_context_management(run: Run, example: Example) -> dict:
    """Evaluates context window management."""
    # Implementation from STEPS.md Step 6...
```

#### 6.3 Update Evaluation Runner

**Files:** `src/evaluation/runner.py`

```python
from src.evaluation.evaluators import (
    evaluate_feature_identification,
    evaluate_comprehensive_retrieval,  # NEW
    evaluate_context_management,  # NEW
    evaluate_tool_usage,
    evaluate_decision_quality,
)

def run_evaluation(dataset_name: str = "investigator-agent-module-8") -> dict:
    results = evaluate(
        run_agent,
        data=dataset_name,
        evaluators=[
            evaluate_feature_identification,
            evaluate_comprehensive_retrieval,
            evaluate_context_management,
            evaluate_tool_usage,
            evaluate_decision_quality,
        ],
        experiment_prefix="module-8-eval"
    )
    return results
```

**Acceptance Criteria:**
- ✅ Module 8 evaluation dataset created
- ✅ Scenarios test comprehensive retrieval
- ✅ Scenarios test context management
- ✅ Scenarios test tool selection
- ✅ New evaluators implemented
- ✅ Can run evals via CLI
- ✅ Achieves >75% overall pass rate
- ✅ Achieves >85% on context management
- ✅ Results viewable in LangSmith UI

---

## Validation Checklist (Final)

After completing all steps, verify:

### Code Quality
- [ ] All unit tests pass (`pytest src/ -v`)
- [ ] All integration tests pass (`pytest tests/ -v`)
- [ ] No deprecation warnings
- [ ] No linting errors
- [ ] Type hints present and correct
- [ ] Documentation strings for all functions

### Functionality
- [ ] Agent retrieves all 5 metrics types
- [ ] Agent retrieves all 3 review types
- [ ] Agent can list, read, and search planning docs
- [ ] Agent prefers search over read for targeted queries
- [ ] ConversationSummaryMemory prevents context overflow
- [ ] Agent maintains coherence across memory boundaries
- [ ] Agent makes decisions based on comprehensive data
- [ ] Agent handles missing/ambiguous data gracefully

### Observability
- [ ] All tools emit trace spans
- [ ] Planning doc operations show sizes
- [ ] Ripgrep searches logged
- [ ] Memory operations tracked
- [ ] Conversation spans show retrieval volumes
- [ ] Can analyze traces for retrieval patterns

### Evaluation
- [ ] Module 8 dataset created in LangSmith
- [ ] New evaluators assess retrieval and context management
- [ ] Can run evaluations via CLI
- [ ] Achieves >75% overall pass rate
- [ ] Results viewable in LangSmith UI

### Documentation
- [ ] README explains Module 8 focus
- [ ] .env.example includes memory config
- [ ] Code is self-documenting
- [ ] Comments explain "why" not "what"

---

## Common Pitfalls to Avoid

1. **Reading full docs when search would suffice** - Wastes context
2. **Not testing with multiple large docs** - Won't stress context management
3. **Skipping memory verification** - Won't know if summarization works
4. **Ignoring trace analysis** - Missing insights into retrieval patterns
5. **Not testing multi-turn conversations** - Memory needs multiple turns
6. **Forgetting ripgrep installation** - Tool will fail without it

---

## Success Criteria Summary

Module 8 agent is complete when:

- ✅ Supports all 8 analysis types (5 metrics + 3 reviews)
- ✅ Can list, read, and search planning documents
- ✅ Uses ConversationSummaryMemory for context management
- ✅ Handles large document volumes without overflow
- ✅ Retrieves comprehensive data for assessments
- ✅ Makes decisions based on multiple sources
- ✅ Uses ripgrep efficiently for document search
- ✅ Comprehensive observability for all operations
- ✅ Passes evaluation suite with >75% accuracy
- ✅ Demonstrates effective context management

**Key Learning Outcomes:**
1. Managing large volumes of retrieved data
2. Preventing context window overflow
3. Intelligent tool selection (search vs read)
4. Multi-source decision making
5. Conversation coherence with memory

---

**Remember:** Quality over speed. Build incrementally, test thoroughly, commit often.
