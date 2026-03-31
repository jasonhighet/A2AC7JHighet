# Investigator Agent Design Specification

## Use Case: Feature Readiness Assessment with Comprehensive Data Retrieval

**System Context:** Modern software development teams deploy features through multiple environments in a progression: Development → User Acceptance Testing (UAT) → Production. Each transition requires careful assessment of feature stability, test results, documentation completeness, and risk factors. As features grow in complexity, the volume of relevant data (metrics, reviews, planning documents, code changes) can easily exceed an agent's context window.

**Agent Role:** The Investigator Agent serves as an automated assessor, retrieving and analyzing feature metadata, test metrics, reviews, and planning documentation to provide readiness recommendations for any phase transition in the pipeline. The agent must intelligently manage its context window when dealing with large volumes of retrieved data.

**Scenario:**
When a product manager asks "Is the reservation feature ready for its next phase?", the agent:
1. **Looks up feature metadata** - retrieves Jira ticket, GitHub PR, current status, and context
2. **Retrieves comprehensive analysis data** - examines metrics (tests, performance, security), reviews (security, UAT, stakeholders), and planning documentation
3. **Manages context intelligently** - summarizes older conversation turns and large documents to stay within token limits
4. **Makes recommendation** - provides clear guidance with reasoning for the next appropriate phase

**Example Interactions:**

*Development → UAT Assessment:*
```
User: "Is the reservation feature ready for its next phase?"

Agent: I found the reservation feature (FEAT-RS-003) currently in Development status.

Let me gather comprehensive data about this feature...

[Agent retrieves: JIRA metadata, 5 metrics files, 3 review files, 7 planning documents]
[Agent uses ConversationSummaryMemory to manage context as data accumulates]

✅ **READY FOR UAT** - Feature meets criteria for User Acceptance Testing.

**Analysis:**
- All 156 unit tests passing (100% success rate)
- Test coverage at 87% (exceeds 80% requirement)
- Code review completed and PR merged
- Security scan shows LOW risk
- Performance benchmarks within acceptable range
- All required planning documents present and current

**Recommendation:** Move to UAT environment for user testing.
```

*UAT → Production Assessment with Context Management:*
```
User: "Tell me about the QR code check-in feature. Is it ready for production?"

Agent: I found the QR code check-in feature (FEAT-QR-002) currently in UAT status.

Retrieving comprehensive data... This feature has extensive documentation and review history.

[Agent retrieves large planning docs, multiple test reports, review history]
[ConversationSummaryMemory summarizes earlier conversation context]
[Agent searches planning docs using ripgrep for specific criteria]

❌ **NOT READY FOR PRODUCTION** - Critical issues prevent production deployment.

**Key Blockers:**
- 2 failed tests including HIGH severity race condition
- Critical bug: Multiple users can check in with same QR code simultaneously
- Security review shows MEDIUM risk with 3 unresolved findings
- Performance benchmarks show P95 latency exceeding threshold under load
- UAT feedback indicates 2 critical usability issues

**Test Results:** 485/487 tests passing (99.59%) - normally excellent, but the 2 failures are blockers.

**Recommendation:** Fix PLAT-1823 (race condition), resolve security findings, and address performance issues before production deployment.
```

## Module 8 Focus: Retrieval and Context Management

This module builds upon the basic agent from Module 7, adding capabilities to:

1. **Retrieve comprehensive data from multiple sources**
   - Expanded analysis tools (8 types: 5 metrics + 3 reviews)
   - Planning document access (list, read, search)
   - Large document handling

2. **Manage context window intelligently**
   - Use LangChain's ConversationSummaryMemory to prevent context overflow
   - Handle large planning documents that would otherwise exceed limits
   - Summarize older conversation history while retaining key information

3. **Search and filter relevant information**
   - Ripgrep integration for semantic search across planning docs
   - Targeted retrieval to avoid loading unnecessary data

**Key Learning Objectives:**
- Understanding context window limitations
- Implementing conversation memory strategies
- Managing large volumes of retrieved data
- Balancing comprehensiveness with context constraints

## Acceptance Criteria

Your implementation must satisfy these specific requirements to be considered complete:

### Core Functionality (from Module 7)
- **GIVEN** the agent can be initialized without incident,
  - **WHEN** "Is the reservation feature ready for its next phase?" is submitted in the input field,
  - **THEN** the agent should respond with the feature's correct status and next phase recommendation.

### Feature Matching & Error Handling (from Module 7)
- **GIVEN** the agent has access to some features,
  - **WHEN** a feature that should not match is submitted,
  - **THEN** the response should say it can't find a feature that confidently matches that description
  - **AND** the response should ask the user for more details about the feature

### Comprehensive Data Retrieval (New in Module 8)
- **GIVEN** the agent needs to assess a feature's readiness
  - **WHEN** asked about a specific feature
  - **THEN** the agent should retrieve all relevant analysis types:
    - All 5 metrics types (test_coverage, pipeline, performance, security_scan, unit_tests)
    - All 3 review types (security review, UAT review, stakeholder approvals)
    - Relevant planning documents when needed for clarification
  - **AND** use the appropriate tool for each data type

### Planning Document Access (New in Module 8)
- **GIVEN** the agent needs additional context about a feature
  - **WHEN** planning documentation would provide relevant information
  - **THEN** the agent should:
    - List available planning documents for the feature
    - Read specific documents when needed
    - Use ripgrep to search documents for specific information
    - Extract relevant sections without overwhelming context

### Context Window Management (New in Module 8)
- **GIVEN** the agent is processing large amounts of data
  - **WHEN** conversation history and retrieved data approach context limits
  - **THEN** the agent should:
    - Use ConversationSummaryMemory to summarize older messages
    - Continue functioning effectively without losing critical context
    - Maintain coherent conversation across multiple turns
    - Not truncate or lose important decision-making information

### Decision Making (from Module 7, Enhanced)
- **GIVEN** an agent can successfully retrieve comprehensive feature data
  - **WHEN** there are any failing tests OR critical security findings OR UAT blockers
  - **THEN** the agent should recommend the feature not progress to the next phase
  - **AND** provide specific reasoning citing all relevant data sources
- **GIVEN** an agent can successfully retrieve comprehensive feature data
  - **WHEN** all quality gates pass (tests, reviews, documentation)
  - **THEN** the agent should recommend progression to the next phase
  - **AND** cite evidence from multiple data sources (metrics, reviews, planning)

## Agent Architecture

### Core Workflow
```
User Query → Feature Identification → Comprehensive Data Retrieval → Context Management → Analysis → Phase Readiness Decision
```

### Required Tools

#### From Module 7 (Already Implemented)
1. **Feature Metadata Lookup** - Retrieves feature information from Jira, GitHub, planning docs, current status

#### New in Module 8

2. **Metrics Analysis Tools** - 5 types:
   - `metrics/test_coverage_report` - Code coverage percentages and gaps
   - `metrics/pipeline_results` - CI/CD pipeline execution results
   - `metrics/performance_benchmarks` - Performance test results
   - `metrics/security_scan_results` - Automated security scan findings
   - `metrics/unit_test_results` - Unit test execution summary

3. **Review Analysis Tools** - 3 types:
   - `reviews/security` - Security review results, vulnerabilities, compliance
   - `reviews/uat` - User acceptance testing results and feedback
   - `reviews/stakeholders` - Stakeholder approval records and sign-offs

4. **Planning Document Tools** - 3 capabilities:
   - `list_planning_docs(feature_id)` - List all planning documents for a feature
   - `read_planning_doc(feature_id, doc_name)` - Read a specific planning document
   - `search_planning_docs(feature_id, query)` - Search planning docs using ripgrep

### Context Management Strategy

**Challenge:** A single feature can have 15+ documents (7 planning docs, 5 metrics, 3 reviews), some quite large (10-15KB each). Asking about 2-3 features simultaneously can easily exceed context windows.

**Solution:** LangChain's `ConversationSummaryMemory`

**How It Works:**
```python
from langchain.memory import ConversationSummaryMemory
from langchain_anthropic import ChatAnthropic

# Memory automatically summarizes old messages when buffer gets large
memory = ConversationSummaryMemory(
    llm=ChatAnthropic(model="claude-3-5-sonnet-20241022"),
    max_token_limit=2000,  # When to start summarizing
    return_messages=True
)

# As conversation grows, older messages are summarized
# Recent messages stay intact for context
# Summary is prepended to maintain continuity
```

**Benefits:**
- **Automatic**: No manual intervention needed
- **Intelligent**: Uses LLM to create meaningful summaries
- **Preserves continuity**: Summaries maintain conversation flow
- **Configurable**: Adjust token threshold based on model limits

**When It Activates:**
- After retrieving multiple large planning documents
- When analyzing several features in one conversation
- After extensive back-and-forth about a complex feature
- When accumulated context approaches token limits

## Success Metrics

The agent is complete when it:
- ✅ Correctly identifies features from natural language descriptions
- ✅ Retrieves all relevant data types (5 metrics + 3 reviews + planning docs as needed)
- ✅ Makes appropriate phase progression decisions based on comprehensive data
- ✅ Uses planning document tools effectively (list, read, search)
- ✅ Manages context window using ConversationSummaryMemory
- ✅ Maintains conversation coherence across multiple turns with large data volumes
- ✅ Handles missing/ambiguous data gracefully with helpful error messages
- ✅ Provides clear reasoning for all decisions with specific evidence from multiple sources
- ✅ Includes comprehensive observability and error handling
- ✅ Demonstrates retry logic for transient failures
- ✅ Passes automated evaluation suite with >85% accuracy across all acceptance criteria

## Additional Capabilities (Extracurricular - Not Required for Exercise)

The project includes infrastructure for advanced retrieval capabilities:

### Vector Database (Chroma)
- **Purpose**: Semantic search across planning documentation
- **Setup**: Docker Compose + ingestion scripts provided
- **Use Case**: "Find all planning docs mentioning authentication flows"
- **Status**: Infrastructure provided for demonstration and experimentation

### Graph Database (Neo4j)
- **Purpose**: Code AST storage and relationship queries
- **Setup**: Docker Compose + ingestion scripts provided
- **Use Case**: "Show all functions modified in this feature's commits"
- **Status**: Infrastructure provided for demonstration and experimentation

### MCP Servers
- **Purpose**: Standardized tool protocols
- **Setup**: Examples provided for Chroma MCP, Neo4j MCP, Graphiti MCP
- **Status**: Optional extension for interested students

**Note:** These capabilities demonstrate the "art of the possible" but are not required to complete the module. The primary learning objectives focus on context management with direct file access and ripgrep search.
