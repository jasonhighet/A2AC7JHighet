# Investigator Agent Implementation Steps

## Prerequisites

This module assumes you have completed Module 7 and have a working LangChain agent with:
- ✅ CLI interface for agent interaction
- ✅ LangGraph workflow with agent and tools nodes
- ✅ Basic JIRA tool (`get_jira_data`)
- ✅ Basic analysis tool supporting 2 types:
  - `metrics/unit_test_results`
  - `metrics/test_coverage_report`
- ✅ OpenTelemetry tracing
- ✅ Retry logic with exponential backoff
- ✅ LangSmith evaluation setup

If you don't have this starting point, an example implementation is provided in the `module-07-complete/` directory.

### Quick Start
- **Step 1**: Add comprehensive metrics analysis (5 types total)
- **Step 2**: Add review analysis tools (3 types)
- **Step 3**: Add planning document tools (list, read, search)
- **Step 4**: Implement context window management (ConversationSummaryMemory)
- **Step 5**: Update observability for new tools
- **Step 6**: Update evaluations for comprehensive retrieval

---

## Step 1: Add Comprehensive Metrics Analysis

**Goal:** Expand analysis tool to support all 5 metrics types

**What You'll Build:**
- Support for 3 additional metrics types:
  - `metrics/pipeline_results`
  - `metrics/performance_benchmarks`
  - `metrics/security_scan_results`
- Updated system prompt with guidance for using all metrics
- Enhanced decision logic considering all metrics

**Current State (From Module 7):**
```python
@tool
def get_analysis(feature_id: str, analysis_type: str) -> Dict[str, Any]:
    """Retrieves analysis data for a specific feature.
    
    Currently supports:
    - metrics/unit_test_results
    - metrics/test_coverage_report
    """
```

**Target State (After Step 1):**
```python
@tool
def get_analysis(feature_id: str, analysis_type: str) -> Dict[str, Any]:
    """Retrieves analysis data for a specific feature.
    
    Metrics types:
    - metrics/unit_test_results - Unit test execution summary
    - metrics/test_coverage_report - Code coverage statistics
    - metrics/pipeline_results - CI/CD pipeline execution results
    - metrics/performance_benchmarks - Performance test results
    - metrics/security_scan_results - Automated security scan findings
    """
```

**System Prompt Updates:**
Add to the decision criteria section:
```
## Comprehensive Analysis Requirements

When assessing feature readiness, you should retrieve ALL relevant metrics:

**Core Metrics (Always Required):**
- metrics/unit_test_results - Check for test failures
- metrics/test_coverage_report - Verify coverage meets threshold (80%+)

**Additional Metrics (Stage-Dependent):**
- metrics/pipeline_results - Verify CI/CD success
- metrics/security_scan_results - Check for vulnerabilities
- metrics/performance_benchmarks - Verify performance criteria

**Decision Rules:**
- Development → UAT:
  ✅ All unit tests passing
  ✅ Coverage ≥ 80%
  ✅ Pipeline successful
  ✅ Security scan shows LOW or MEDIUM risk (HIGH = blocker)

- UAT → Production:
  ✅ All unit tests passing
  ✅ Coverage ≥ 80%
  ✅ Pipeline successful
  ✅ Security scan shows LOW risk only
  ✅ Performance benchmarks meet SLA requirements
```

**Success Criteria:**
- ✅ Tool accepts all 5 metrics types
- ✅ Agent retrieves multiple metrics when assessing readiness
- ✅ Agent decision logic considers pipeline results
- ✅ Agent decision logic considers security scan results
- ✅ Agent decision logic considers performance benchmarks
- ✅ Agent cites specific findings from multiple metrics in responses
- ✅ Unit tests verify all 5 metrics types work correctly
- ✅ Integration tests verify multi-metric decision making

**Test Conversation:**
```
You: Is the maintenance scheduling feature ready for production?

Expected:
- Agent calls get_jira_data()
- Agent calls get_analysis for unit_test_results
- Agent calls get_analysis for test_coverage_report
- Agent calls get_analysis for pipeline_results
- Agent calls get_analysis for security_scan_results
- Agent calls get_analysis for performance_benchmarks
- Agent synthesizes all metrics into readiness decision
- Agent cites specific data from each metric type

Example response:
"✅ READY FOR PRODUCTION

Analysis:
- Unit Tests: 156/156 passing (100%)
- Test Coverage: 87% (exceeds 80% requirement)
- Pipeline: Build #342 successful, all stages passed
- Security: LOW risk, no critical vulnerabilities found
- Performance: P95 latency 145ms (under 200ms SLA)

Recommendation: Feature meets all production criteria."
```

---

## Step 2: Add Review Analysis Tools

**Goal:** Add support for 3 review types (security, UAT, stakeholder approvals)

**What You'll Build:**
- Support for review analysis types:
  - `reviews/security`
  - `reviews/uat`
  - `reviews/stakeholders`
- Updated system prompt with review criteria
- Decision logic incorporating human review outcomes

**Implementation:**
The existing `get_analysis` tool already supports any `analysis_type` parameter. You just need to:
1. Update the tool's docstring to document review types
2. Update the system prompt to guide when to use reviews
3. Verify the data files exist in `data/incoming/feature*/reviews/`

**Updated Tool Docstring:**
```python
@tool
def get_analysis(feature_id: str, analysis_type: str) -> Dict[str, Any]:
    """Retrieves analysis data for a specific feature.
    
    Metrics types:
    - metrics/unit_test_results
    - metrics/test_coverage_report
    - metrics/pipeline_results
    - metrics/performance_benchmarks
    - metrics/security_scan_results
    
    Review types:
    - reviews/security - Security review results, vulnerabilities, compliance
    - reviews/uat - User acceptance testing feedback and approval status
    - reviews/stakeholders - Stakeholder sign-offs and approvals
    """
```

**System Prompt Updates:**
```
## Review Analysis

In addition to metrics, you should check review outcomes:

**Security Review:**
- Status: APPROVED / IN_REVIEW / REJECTED
- Overall risk level: LOW / MEDIUM / HIGH / CRITICAL
- Findings: List of security issues discovered
- Required for: UAT → Production transitions

**UAT Review:**
- Status: PASSED / IN_PROGRESS / FAILED
- Tester feedback: Individual tester comments
- Critical issues found: Blockers identified during UAT
- Required for: UAT → Production transitions

**Stakeholder Review:**
- Product Manager approval: YES / NO / PENDING
- Engineering Lead approval: YES / NO / PENDING  
- Community Manager approval: YES / NO / PENDING
- Required for: All production deployments

**Decision Rules:**
- UAT → Production requires:
  ✅ Security review APPROVED with LOW risk
  ✅ UAT review PASSED with no critical issues
  ✅ All required stakeholder approvals obtained
```

**Success Criteria:**
- ✅ Tool accepts all 3 review types
- ✅ Agent retrieves reviews when assessing production readiness
- ✅ Agent blocks progression if security review shows HIGH/CRITICAL risk
- ✅ Agent blocks progression if UAT has critical issues
- ✅ Agent blocks progression if stakeholder approvals are missing
- ✅ Agent cites specific review findings in responses
- ✅ Unit tests verify all 3 review types work correctly
- ✅ Integration tests verify review-based blocking

**Test Conversation:**
```
You: Is the QR code check-in feature ready for production?

Expected:
- Agent calls get_jira_data()
- Agent calls get_analysis for all 5 metrics
- Agent calls get_analysis for security review
- Agent calls get_analysis for UAT review
- Agent calls get_analysis for stakeholders review
- Agent identifies blockers from reviews
- Agent makes NOT READY decision based on review findings

Example response:
"❌ NOT READY FOR PRODUCTION

Blockers:
- Security Review: MEDIUM risk with 3 unresolved findings
  * Finding #1: QR code invalidation logic vulnerable to race conditions
  * Finding #2: JWT token expiry not validated on check-in
  * Finding #3: Rate limiting missing on QR generation endpoint
  
- UAT Review: 2 critical issues identified
  * Mobile app crashes when QR code expires during scan
  * Check-in fails silently when offline

- Stakeholder Approvals: INCOMPLETE
  * Product Manager: APPROVED
  * Engineering Lead: PENDING (waiting for security fixes)
  * Community Manager: PENDING

Recommendation: Address security findings and UAT critical issues before production."
```

---

## Step 3: Add Planning Document Tools

**Goal:** Enable agent to access planning documentation when needed

**What You'll Build:**
- Tool to list available planning documents
- Tool to read specific planning documents
- Tool to search planning documents using ripgrep
- Context management awareness (planning docs can be large)

**Why This Step:**
Some readiness assessments require understanding the original requirements or architecture decisions. Planning documents provide this context but can be quite large (10-15KB each), creating context pressure.

**New Tools:**

```python
@tool
def list_planning_docs(feature_id: str) -> List[str]:
    """List all planning documents available for a feature.
    
    Args:
        feature_id: The feature ID (e.g., 'FEAT-MS-001')
    
    Returns:
        List of document names (e.g., ['USER_STORY.md', 'DESIGN_DOC.md', ...])
    
    Use this to:
    - See what documentation exists for a feature
    - Determine which documents to read for specific information
    - Avoid reading unnecessary large documents
    """

@tool  
def read_planning_doc(feature_id: str, doc_name: str) -> str:
    """Read a specific planning document.
    
    Args:
        feature_id: The feature ID (e.g., 'FEAT-MS-001')
        doc_name: Document name from list_planning_docs (e.g., 'USER_STORY.md')
    
    Returns:
        Full document content (may be large, 10-15KB)
    
    WARNING: Planning documents can be large. Consider using 
    search_planning_docs if you're looking for specific information.
    """

@tool
def search_planning_docs(feature_id: str, query: str) -> List[Dict[str, str]]:
    """Search planning documents using ripgrep.
    
    Args:
        feature_id: The feature ID (e.g., 'FEAT-MS-001')
        query: Search query (regex supported)
    
    Returns:
        List of matches with filename, line number, and matching text
    
    Use this to:
    - Find specific information across all planning docs
    - Avoid reading entire large documents
    - Locate mentions of specific requirements, APIs, or components
    
    Example query: "authentication" to find all auth-related requirements
    """
```

**Implementation Details:**

For `search_planning_docs`, use Python's `subprocess` to call ripgrep:
```python
import subprocess
import json

def search_planning_docs(feature_id: str, query: str) -> List[Dict[str, str]]:
    # Map feature_id to folder
    folder = get_feature_folder(feature_id)
    planning_path = f"data/incoming/{folder}/planning/"
    
    # Call ripgrep with JSON output
    result = subprocess.run(
        ["rg", "--json", query, planning_path],
        capture_output=True,
        text=True
    )
    
    # Parse ripgrep JSON output
    matches = []
    for line in result.stdout.strip().split('\n'):
        if line:
            data = json.loads(line)
            if data.get('type') == 'match':
                matches.append({
                    'file': data['data']['path']['text'],
                    'line_number': data['data']['line_number'],
                    'match': data['data']['lines']['text'].strip()
                })
    
    return matches
```

**System Prompt Updates:**
```
## Planning Document Tools

You have access to planning documentation for each feature:

**Available Documents:**
- USER_STORY.md - User stories and acceptance criteria
- DESIGN_DOC.md - Detailed design decisions
- ARCHITECTURE.md - System architecture and component design
- API_SPECIFICATION.md - API contracts and endpoints
- DATABASE_SCHEMA.md - Database schema and migrations
- DEPLOYMENT_PLAN.md - Deployment strategy and procedures
- TEST_STRATEGY.md - Testing approach and coverage goals

**Tool Usage Strategy:**

1. **list_planning_docs(feature_id)** - Start here to see what's available
2. **search_planning_docs(feature_id, query)** - Preferred for finding specific info
3. **read_planning_doc(feature_id, doc_name)** - Only when you need full context

**When to Use Planning Docs:**
- User asks about requirements or acceptance criteria
- Need to understand architectural decisions
- Clarifying expected API behavior
- Verifying deployment prerequisites
- Understanding test strategy

**Context Management Warning:**
Planning documents are LARGE (10-15KB each). Reading multiple full documents 
can quickly fill your context window. Prefer search_planning_docs for targeted 
information retrieval.
```

**Success Criteria:**
- ✅ Can list planning documents for any feature
- ✅ Can read specific planning documents
- ✅ Can search across planning documents with ripgrep
- ✅ Agent uses search when looking for specific information
- ✅ Agent uses read sparingly (only when full context needed)
- ✅ Agent cites planning docs when relevant to readiness assessment
- ✅ Error handling for missing documents
- ✅ Unit tests for all three planning doc tools
- ✅ Integration test showing intelligent tool selection

**Test Conversation:**
```
You: What are the acceptance criteria for the maintenance scheduling feature?

Expected:
- Agent calls list_planning_docs('FEAT-MS-001')
- Agent sees USER_STORY.md is available
- Agent calls search_planning_docs('FEAT-MS-001', 'acceptance criteria')
  (Avoids reading full 15KB USER_STORY.md)
- Agent returns specific acceptance criteria found

Example response:
"I found the acceptance criteria in USER_STORY.md:

1. Users can schedule maintenance windows for resources
2. Automated alerts sent 24h before maintenance
3. Resources automatically marked unavailable during maintenance
4. Maintenance history logged and viewable
5. Recurring maintenance schedules supported

These criteria come from the user story planning document."
```

---

## Step 4: Implement Context Window Management

**Goal:** Add ConversationSummaryMemory to prevent context overflow

**What You'll Build:**
- LangChain ConversationSummaryMemory integration
- Configuration for summary thresholds
- Testing with large document scenarios
- Observability for when summarization occurs

**The Problem:**
With expanded data retrieval capabilities, the agent can easily exceed context limits:
- 5 metrics files × ~5KB = ~25KB
- 3 review files × ~3KB = ~9KB  
- 7 planning docs × ~12KB = ~84KB (if all read)
- Conversation history = 10-50KB

**Total: Can easily exceed 100KB+ in a single session**

**The Solution: ConversationSummaryMemory**

This LangChain component automatically:
- Monitors token usage in conversation history
- Triggers summarization when threshold exceeded
- Uses LLM to create intelligent summaries of old messages
- Preserves recent messages for immediate context
- Maintains conversation continuity

**Implementation:**

```python
# src/agent/graph.py

from langchain.memory import ConversationSummaryMemory
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, AIMessage

def create_agent_graph(config):
    """Creates the agent graph with memory management."""
    
    # Initialize LLM for both agent and summarization
    llm = ChatAnthropic(
        model=config.MODEL_NAME,
        temperature=config.TEMPERATURE,
        max_tokens=config.MAX_TOKENS
    )
    
    # Initialize ConversationSummaryMemory
    memory = ConversationSummaryMemory(
        llm=llm,
        max_token_limit=2000,  # Start summarizing after 2000 tokens
        return_messages=True,  # Return as message objects, not strings
        memory_key="chat_history"
    )
    
    # Modify agent state to include memory
    class AgentState(TypedDict):
        messages: Annotated[Sequence[BaseMessage], add_messages]
        summary: str  # Conversation summary
    
    def call_model(state: AgentState):
        """Agent node with memory integration."""
        messages = state["messages"]
        
        # Load memory context (includes summary if exists)
        memory_context = memory.load_memory_variables({})
        
        # If there's a summary, prepend it
        if memory_context.get("history"):
            # Summary is already in message format
            messages = memory_context["history"] + list(messages)
        
        # Call LLM
        response = llm_with_tools.invoke(messages)
        
        # Save to memory (will trigger summarization if needed)
        if len(messages) > 0:
            memory.save_context(
                {"input": messages[-1].content if hasattr(messages[-1], 'content') else str(messages[-1])},
                {"output": response.content}
            )
        
        return {"messages": [response]}
    
    # Rest of graph setup...
```

**Configuration:**

Add to `.env` and `config.py`:
```python
# Context management
MEMORY_MAX_TOKEN_LIMIT=2000  # When to start summarizing
MEMORY_STRATEGY=summary  # Options: summary, buffer, sliding_window
```

**System Prompt Updates:**
```
## Context Window Management

You are equipped with conversation memory that automatically summarizes
older parts of the conversation when it gets too long. This allows you to:

- Handle large planning documents without losing context
- Maintain multi-turn conversations about complex features
- Retrieve comprehensive data without context overflow

When you see a conversation summary at the start of messages, that's your
memory system helping you stay within context limits while preserving
important information from earlier in the conversation.
```

**Observability Integration:**

Add spans to track memory operations:
```python
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

def call_model(state: AgentState):
    with tracer.start_as_current_span("agent.call_model") as span:
        # ... existing code ...
        
        # Track if summarization occurred
        memory_vars = memory.load_memory_variables({})
        if "history" in memory_vars and len(memory_vars["history"]) > 0:
            span.set_attribute("memory.summarized", True)
            span.set_attribute("memory.summary_length", len(str(memory_vars["history"])))
        else:
            span.set_attribute("memory.summarized", False)
```

**Success Criteria:**
- ✅ ConversationSummaryMemory initialized and configured
- ✅ Memory integrates with LangGraph workflow
- ✅ Summarization triggers when token threshold exceeded
- ✅ Agent maintains context across summaries
- ✅ Recent messages preserved during summarization
- ✅ Agent can handle reading multiple large planning docs
- ✅ Agent can analyze multiple features in one conversation
- ✅ Observability tracks memory operations
- ✅ Unit tests verify memory behavior
- ✅ Integration tests with large data volumes

**Test Conversation (Context Stress Test):**
```
You: Tell me about the maintenance scheduling feature. What's in the design doc?

Agent: [Calls list_planning_docs, then read_planning_doc for DESIGN_DOC.md]
Agent: [Returns design summary - ~15KB added to context]

You: Now tell me about the QR code check-in feature. Read its architecture doc.

Agent: [Calls list_planning_docs, then read_planning_doc for ARCHITECTURE.md]
Agent: [Returns architecture summary - another ~15KB added]
Agent: [Memory summarizes first exchange to free up context]

You: Compare the two features. Which is ready for production?

Agent: [Calls get_analysis for both features - multiple metrics and reviews]
Agent: [Can still access summary of earlier doc discussions]
Agent: [Makes comparison despite large context usage]

Expected:
- Memory summarizes early doc discussions
- Agent retains key information from summaries
- Agent successfully retrieves and analyzes data for both features
- Agent provides coherent comparison across entire conversation
- Traces show memory.summarized = true
```

---

## Step 5: Update Observability for New Tools

**Goal:** Ensure tracing captures all new tool operations

**What You'll Build:**
- Trace spans for planning document operations
- Span attributes for ripgrep searches
- Memory operation tracking
- Enhanced trace analysis capabilities

**OpenTelemetry Spans to Add:**

```python
# For list_planning_docs
with tracer.start_as_current_span("tool.list_planning_docs") as span:
    span.set_attribute("feature_id", feature_id)
    span.set_attribute("docs_found", len(doc_list))
    span.set_attribute("docs", json.dumps(doc_list))

# For read_planning_doc
with tracer.start_as_current_span("tool.read_planning_doc") as span:
    span.set_attribute("feature_id", feature_id)
    span.set_attribute("doc_name", doc_name)
    span.set_attribute("doc_size_bytes", len(content))
    span.set_attribute("doc_size_kb", len(content) / 1024)

# For search_planning_docs (ripgrep)
with tracer.start_as_current_span("tool.search_planning_docs") as span:
    span.set_attribute("feature_id", feature_id)
    span.set_attribute("query", query)
    span.set_attribute("matches_found", len(matches))
    span.set_attribute("files_searched", len(set(m['file'] for m in matches)))
    span.set_attribute("ripgrep.command", " ".join(cmd))
    span.set_attribute("ripgrep.exit_code", result.returncode)
```

**Enhanced Conversation Span:**

Update the main conversation span to track memory:
```python
with tracer.start_as_current_span("agent.conversation") as span:
    span.set_attribute("conversation_id", conversation_id)
    span.set_attribute("user_message", user_input)
    
    # Track data retrieval volume
    span.set_attribute("metrics_retrieved", metrics_count)
    span.set_attribute("reviews_retrieved", reviews_count)
    span.set_attribute("planning_docs_read", docs_read_count)
    span.set_attribute("planning_docs_searched", searches_count)
    
    # Track context management
    span.set_attribute("memory.summarization_triggered", summarized)
    span.set_attribute("memory.total_tokens_estimate", estimated_tokens)
    
    # Track decision outcome
    span.set_attribute("decision", decision)  # ready / not_ready / needs_info
    span.set_attribute("confidence", confidence)  # high / medium / low
```

**Success Criteria:**
- ✅ All new tools emit trace spans
- ✅ Planning doc operations tracked with sizes
- ✅ Ripgrep searches logged with results
- ✅ Memory operations visible in traces
- ✅ Conversation spans show comprehensive retrieval stats
- ✅ Can analyze trace to understand agent's data access patterns
- ✅ Trace files include all new attributes

**Validation:**
```bash
# Run a test conversation
python cli.py

# Check trace file
cat traces/trace_*.json | jq '.spans[] | select(.name | contains("planning"))'

# Should see:
# - tool.list_planning_docs spans
# - tool.read_planning_doc spans with doc sizes
# - tool.search_planning_docs spans with match counts
# - memory.summarized attributes
```

---

## Step 6: Update Evaluations for Comprehensive Retrieval

**Goal:** Adapt evaluation suite to assess new capabilities

**What You'll Build:**
- Updated test scenarios covering comprehensive retrieval
- New evaluator for planning doc usage
- Enhanced evaluators for multi-metric decisions
- Context management evaluation scenarios

**New Evaluation Dimensions:**

1. **Comprehensive Retrieval Evaluation**
   - Did agent retrieve all relevant metrics? (5 types)
   - Did agent retrieve all relevant reviews? (3 types)
   - Did agent use planning docs when appropriate?
   - Did agent avoid retrieving unnecessary data?

2. **Context Management Evaluation**
   - Did agent handle large documents without context overflow?
   - Did conversation remain coherent after summarization?
   - Did agent retain critical information across summaries?

3. **Tool Selection Evaluation**
   - Did agent use search_planning_docs vs read_planning_doc appropriately?
   - Did agent list docs before reading/searching?
   - Did agent retrieve data in logical order?

**Updated Evaluator:**

```python
# src/evaluation/evaluators.py

def evaluate_comprehensive_retrieval(run: Run, example: Example) -> dict:
    """Evaluates if agent retrieved all necessary data sources.
    
    Checks:
    - Retrieved all required metrics (5 types)
    - Retrieved all required reviews (3 types)
    - Used planning docs when question requires them
    - Avoided unnecessary retrieval
    """
    expected_metrics = example.outputs.get("expected_metrics", [])
    expected_reviews = example.outputs.get("expected_reviews", [])
    should_use_planning = example.outputs.get("should_use_planning_docs", False)
    
    # Extract actual tool calls from run
    tool_calls = [
        child for child in run.child_runs 
        if child.run_type == "tool"
    ]
    
    metrics_retrieved = [
        call for call in tool_calls 
        if call.name == "get_analysis" and "metrics/" in str(call.inputs)
    ]
    
    reviews_retrieved = [
        call for call in tool_calls
        if call.name == "get_analysis" and "reviews/" in str(call.inputs)
    ]
    
    planning_used = any(
        call.name in ["list_planning_docs", "read_planning_doc", "search_planning_docs"]
        for call in tool_calls
    )
    
    # Score based on completeness
    score = 0.0
    comments = []
    
    # Metrics coverage (40%)
    if len(metrics_retrieved) >= len(expected_metrics):
        score += 0.4
        comments.append(f"✓ Retrieved {len(metrics_retrieved)} metrics")
    else:
        comments.append(f"✗ Only retrieved {len(metrics_retrieved)}/{len(expected_metrics)} metrics")
    
    # Reviews coverage (40%)
    if len(reviews_retrieved) >= len(expected_reviews):
        score += 0.4
        comments.append(f"✓ Retrieved {len(reviews_retrieved)} reviews")
    else:
        comments.append(f"✗ Only retrieved {len(reviews_retrieved)}/{len(expected_reviews)} reviews")
    
    # Planning docs usage (20%)
    if should_use_planning == planning_used:
        score += 0.2
        if planning_used:
            comments.append("✓ Used planning docs when needed")
        else:
            comments.append("✓ Correctly skipped planning docs")
    else:
        if should_use_planning:
            comments.append("✗ Should have used planning docs but didn't")
        else:
            comments.append("✗ Used planning docs unnecessarily")
    
    return {
        "key": "comprehensive_retrieval",
        "score": score,
        "comment": " | ".join(comments)
    }


def evaluate_context_management(run: Run, example: Example) -> dict:
    """Evaluates context window management.
    
    Checks:
    - Conversation remained coherent despite large data volumes
    - Agent retained critical information across turns
    - No signs of context overflow or truncation errors
    """
    involves_large_docs = example.outputs.get("involves_large_docs", False)
    
    if not involves_large_docs:
        return {
            "key": "context_management",
            "score": 1.0,
            "comment": "N/A - scenario doesn't stress context window"
        }
    
    # Check for signs of context issues
    response = run.outputs.get("output", "")
    
    # Red flags: incomplete responses, nonsensical answers, tool errors
    context_issues = []
    
    if "..." in response and len(response) < 100:
        context_issues.append("Response appears truncated")
    
    if "error" in response.lower() and "context" in response.lower():
        context_issues.append("Context-related error in response")
    
    # Check if response references earlier conversation appropriately
    references_earlier = any(
        phrase in response.lower() 
        for phrase in ["as mentioned", "earlier", "previously", "as we discussed"]
    )
    
    if involves_large_docs and not references_earlier:
        context_issues.append("No reference to earlier conversation context")
    
    # Score
    if len(context_issues) == 0:
        return {
            "key": "context_management",
            "score": 1.0,
            "comment": "✓ Context managed effectively"
        }
    else:
        return {
            "key": "context_management",
            "score": 0.0,
            "comment": "✗ Context issues: " + ", ".join(context_issues)
        }
```

**Updated Test Scenarios:**

```python
# src/evaluation/scenarios.py

def create_evaluation_dataset() -> str:
    """Creates Module 8 evaluation dataset."""
    
    examples = [
        # Scenario 1: Comprehensive retrieval with all metrics and reviews
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
        
        # Scenario 2: Large docs requiring context management
        {
            "inputs": {
                "user_query": "What are the acceptance criteria for the QR code check-in feature? Then assess if it's ready for production."
            },
            "outputs": {
                "expected_decision": "not_ready",
                "expected_feature": "FEAT-QR-002",
                "should_use_planning_docs": True,
                "involves_large_docs": True,
                "expected_metrics": ["metrics/unit_test_results", "metrics/security_scan_results"],
                "expected_reviews": ["reviews/security", "reviews/uat"]
            },
            "metadata": {"category": "context_management", "difficulty": "hard"}
        },
        
        # Scenario 3: Multi-feature comparison stressing context
        {
            "inputs": {
                "user_query": "Compare the reservation system and QR code features. Which is closer to production ready?"
            },
            "outputs": {
                "involves_large_docs": True,
                "expected_features": ["FEAT-RS-003", "FEAT-QR-002"],
                "should_retrieve_multiple_features": True
            },
            "metadata": {"category": "context_stress", "difficulty": "hard"}
        },
        
        # Scenario 4: Planning doc search vs read
        {
            "inputs": {
                "user_query": "Does the maintenance scheduling feature's architecture mention WebSocket support?"
            },
            "outputs": {
                "expected_feature": "FEAT-MS-001",
                "should_use_planning_docs": True,
                "should_prefer_search": True  # Should use search_planning_docs, not read
            },
            "metadata": {"category": "tool_selection", "difficulty": "medium"}
        },
        
        # Add 4+ more scenarios covering edge cases...
    ]
    
    # Create dataset in LangSmith
    client = Client()
    dataset_name = "investigator-agent-module-8"
    
    dataset = client.create_dataset(
        dataset_name=dataset_name,
        description="Module 8: Comprehensive retrieval and context management"
    )
    
    client.create_examples(
        inputs=[ex["inputs"] for ex in examples],
        outputs=[ex["outputs"] for ex in examples],
        metadata=[ex["metadata"] for ex in examples],
        dataset_id=dataset.id
    )
    
    return dataset_name
```

**Update Evaluation Runner:**

```python
# src/evaluation/runner.py

from src.evaluation.evaluators import (
    evaluate_feature_identification,
    evaluate_tool_usage,
    evaluate_decision_quality,
    evaluate_comprehensive_retrieval,  # New
    evaluate_context_management,  # New
)

def run_evaluation(dataset_name: str = "investigator-agent-module-8") -> dict:
    """Runs Module 8 evaluation."""
    
    results = evaluate(
        run_agent,
        data=dataset_name,
        evaluators=[
            evaluate_feature_identification,
            evaluate_comprehensive_retrieval,  # New evaluator
            evaluate_context_management,  # New evaluator
            evaluate_tool_usage,
            evaluate_decision_quality,
        ],
        experiment_prefix="module-8-eval",
        max_concurrency=2
    )
    
    return results
```

**Success Criteria:**
- ✅ Evaluation dataset includes Module 8 scenarios
- ✅ New evaluators assess comprehensive retrieval
- ✅ New evaluators assess context management
- ✅ Test scenarios include large doc handling
- ✅ Test scenarios include multi-feature conversations
- ✅ Can run evaluations via CLI
- ✅ Achieves >75% pass rate on comprehensive retrieval
- ✅ Achieves >85% pass rate on context management
- ✅ All evaluators execute successfully
- ✅ Results viewable in LangSmith UI

**Validation:**
```bash
# Create new dataset
python cli.py --create-dataset

# Run Module 8 evaluation
python cli.py --eval

# View results in LangSmith UI
# Check pass rates for:
# - comprehensive_retrieval
# - context_management
# - tool_usage (should be >95% with all tools working)
# - decision_quality (should be >85%)
```

---

## Success Progression

**After Step 1:** You have comprehensive metrics analysis (5 types) ✅
**After Step 2:** You have complete review analysis (3 types) ✅  
**After Step 3:** You have planning document access (list, read, search) ✅
**After Step 4:** You have intelligent context window management ✅
**After Step 5:** You have complete observability for all operations ✅
**After Step 6:** You have comprehensive evaluation suite ✅

Each step builds incrementally while maintaining working functionality. After Step 3, you have all data access capabilities. Step 4 is critical for handling the context pressure created by Steps 1-3. Steps 5-6 ensure production readiness.

---

## Module Completion Checklist

The Investigator Agent is ready for Module 8 completion when:

- ✅ Supports all 8 analysis types (5 metrics + 3 reviews)
- ✅ Can list, read, and search planning documents
- ✅ Uses ConversationSummaryMemory for context management
- ✅ Handles large document volumes without context overflow
- ✅ Retrieves comprehensive data for readiness assessments
- ✅ Makes decisions based on metrics, reviews, and planning docs
- ✅ Uses ripgrep for efficient document searching
- ✅ Comprehensive observability for all operations
- ✅ Passes evaluation suite with >75% overall accuracy
- ✅ Demonstrates effective context management in traces

**Key Learning Outcomes Demonstrated:**
1. Managing large volumes of retrieved data
2. Preventing context window overflow
3. Intelligent tool selection (search vs read)
4. Comprehensive multi-source decision making
5. Conversation coherence across memory summarization
