# Module 8 Project: Investigator Agent - Retrieval and Context Management

**System Context:**

The Investigator Agent is part of the Release Confidence System team that helps build confidence in software releases by investigating changes, assessing risks, and producing actionable reports. This agent inspects the state of a feature and determines if it is sufficiently prepared to be promoted to the next stage of development. For example, from the Development environment to UAT, or from UAT to production.

In Module 7, you built the foundational agent with basic data retrieval capabilities. In Module 8, you'll expand the agent to handle comprehensive data retrieval from multiple sources while managing the context window effectively when dealing with large volumes of data.

## Module 8 Focus: Context Window Management

**The Challenge:** As agents retrieve more data from multiple sources (metrics files, review documents, large planning docs), they quickly approach or exceed their context window limits. A single feature assessment can involve:
- 5 metrics files (~5KB each)
- 3 review documents (~3KB each)
- 7 planning documents (~10-15KB each)
- Conversation history (~10-50KB)

**Total: Easily 100KB+ of context**

**The Learning Objective:** Learn to manage context windows using LangChain's built-in memory strategies, enabling your agent to handle large data volumes while maintaining conversation coherence.

## Prerequisites

This module assumes you have completed Module 7 and have a working LangChain agent with:
- ✅ CLI interface for agent interaction
- ✅ LangGraph workflow with agent and tools nodes
- ✅ JIRA tool for feature metadata lookup
- ✅ Analysis tool supporting 2 metrics types (unit tests, test coverage)
- ✅ OpenTelemetry tracing
- ✅ Retry logic with exponential backoff
- ✅ LangSmith evaluation setup

**If you don't have a Module 7 agent:** An example starting point is provided in `module-07-complete/`. You can use this as your foundation.

## What You'll Build in Module 8

You will expand your Module 7 agent with:

1. **Comprehensive Analysis Tools**
   - Support for all 5 metrics types (add 3 more)
   - Support for all 3 review types (new capability)
   - Enhanced decision logic using all data sources

2. **Planning Document Access**
   - Tool to list planning documents
   - Tool to read specific documents
   - Tool to search documents using ripgrep
   - Intelligent tool selection (search vs read)

3. **Context Window Management**
   - LangChain's ConversationSummaryMemory
   - Automatic summarization of older conversation turns
   - Coherent conversation across memory boundaries
   - Large document handling without context overflow

4. **Enhanced Observability**
   - Tracing for all new tools
   - Memory operation tracking
   - Data retrieval volume metrics

5. **Updated Evaluations**
   - Scenarios testing comprehensive retrieval
   - Context management evaluation
   - Multi-source decision making

## Acceptance Criteria

Your expanded agent must satisfy these requirements:

### Can retrieve comprehensive analysis data
**Acceptance Criteria:**
- Analysis tool retrieves all 5 metrics types:
  - metrics/test_coverage_report: Test coverage statistics
  - metrics/unit_test_results: Unit test results
  - metrics/pipeline_results: CI/CD pipeline execution
  - metrics/performance_benchmarks: Performance test results
  - metrics/security_scan_results: Security scan findings
- Analysis tool retrieves all 3 review types:
  - reviews/security: Security review results and risk assessment
  - reviews/uat: User acceptance testing feedback
  - reviews/stakeholders: Stakeholder approval records
- Agent retrieves multiple analysis types when assessing features
- Agent incorporates all relevant data into decisions
- Tool handles missing files gracefully
- Automated tests verify all 8 analysis types

### Can access planning documentation
**Acceptance Criteria:**
- Agent can list planning documents for a feature
- Agent can read specific planning documents
- Agent can search planning documents using ripgrep
- Agent prefers search over read for targeted information
- Agent uses planning docs to answer requirements questions
- Agent cites planning docs when relevant to decisions
- Tools handle missing documents gracefully
- Automated tests verify all planning doc operations

### Manages context window effectively
**Acceptance Criteria:**
- ConversationSummaryMemory configured and integrated
- Memory automatically summarizes old messages when threshold exceeded
- Agent maintains conversation coherence across summarization
- Agent can analyze multiple features in one conversation
- Agent can read multiple large planning docs without overflow
- Agent retains critical information from summarized content
- Observability tracks memory operations
- Automated tests verify context management behavior

### Makes comprehensive readiness decisions
**Acceptance Criteria:**
- Agent retrieves all relevant metrics for the target stage
- Agent retrieves all relevant reviews for the target stage
- Agent uses planning docs when needed for context
- Agent blocks progression on critical issues from any source
- Agent provides detailed reasoning citing multiple sources
- Agent handles missing data gracefully
- Manual testing shows comprehensive assessments

### Can be evaluated
**Evaluation Dimensions:**
1. Feature Identification Evaluation (from Module 7)
2. Comprehensive Retrieval Evaluation (new in Module 8)
3. Context Management Evaluation (new in Module 8)
4. Tool Usage Evaluation (expanded for Module 8)
5. Decision Quality Evaluation (expanded for Module 8)

**Evaluation Acceptance Criteria:**
- Eval framework runs test scenarios automatically
- Comprehensive retrieval evaluated for completeness
- Context management evaluated for coherence
- Tool selection evaluated (search vs read preferences)
- Decision quality measured against expected outcomes
- Structured JSON reports generated for automation
- At least 75% of scenarios pass overall
- At least 85% pass on context management specifically
- Documentation explains how to add new eval cases
- Supports baseline establishment and comparison

### Observability
**Observability Acceptance Criteria:**
- All new tools traced with timing and parameters
- Planning doc operations show document sizes
- Ripgrep searches logged with match counts
- Memory operations visible in traces (summarization events)
- Conversation spans show data retrieval volumes
- Can correlate tool calls to decisions via trace IDs
- Trace files show complete workflow for complex retrievals

## Building Your Agent

This exercise has 2 main parts:
1. Review the implementation plan
2. Iteratively follow the steps in the plan

Everything you and your assistant need to know to implement the expanded Investigator Agent is in `DESIGN.md`. We also recommend a specific order when adding capabilities. Inside `STEPS.md` you'll find an order of implementation that builds incrementally on your Module 7 agent.

We've also provided `PLAN.md` which is an example starter file that a Python developer might use. Feel free to edit this file according to your preferences and language choice. Once you're happy with it, you're ready to begin.

## Test Data

**Important:** The test data is already provided in the `data/incoming/` directory. You do NOT need to create it.

The test data includes **4 features** with different readiness scenarios:

| Feature | Complexity | Stage | Readiness | Description |
|---------|-----------|-------|-----------|-------------|
| **Maintenance Scheduling & Alert System** | Medium | Production-Ready | ✅ READY | Clear success case - all gates passed, complete docs, green metrics |
| **QR Code Check-in/out with Mobile App** | High | Development/UAT | ❌ NOT READY | Multiple blockers - clear failures in testing and implementation |
| **Advanced Resource Reservation System** | High | UAT | 🔄 AMBIGUOUS | Mixed signals - incomplete data, requires judgment |
| **Contribution Tracking & Community Credits** | Medium-High | UAT | 🔄 PARTIAL | Right stage but not ready for next - some gaps remain |

Each feature in `data/incoming/featureN/` includes:
- `jira/`: JIRA metadata (feature_issue.json, issue_changelog.json)
- `metrics/`: 5 different JSON metric files
  - performance_benchmarks.json
  - pipeline_results.json
  - security_scan_results.json
  - test_coverage_report.json
  - unit_test_results.json
- `reviews/`: 3 different JSON review files
  - security.json
  - stakeholders.json
  - uat.json
- `planning/`: Multiple markdown documentation files (7-10 files per feature)
  - USER_STORY.md
  - DESIGN_DOC.md (large, >10KB)
  - ARCHITECTURE.md (large, >10KB)
  - API_SPECIFICATION.md
  - DATABASE_SCHEMA.md (large)
  - DEPLOYMENT_PLAN.md
  - TEST_STRATEGY.md
  - And more...

**Total data size per feature:** Approximately 100-150KB when all files retrieved

The data is synthetic, but intentionally realistic and specifically designed to challenge the agent's context management capabilities.

## Steps

### Step 1: Review the implementation plan

The first step is to review the plan you're going to use going forward. Open `PLAN.md` and read through it. Consider:
- Are the tasks broken down to sufficient detail to avoid overwhelm during implementation?
- Does it follow the same STEPS order?
- Does the technical stack match your preferences?
- Anything you want to adjust before starting?

You may need to collaborate with your assistant to get the planning doc where you're happy with it.

### Step 2: Iterate over the steps in the plan

This is where you get to decide how much you want to bite off at a time. When you're considering the next piece of work, if it doesn't have enough detail, or if it needs to be broken down further, work with your assistant to update PLAN.md until you're happy with what you know it's going to build.

Here is an example prompt that is a good one to start each step with:

#### Remember to: START EACH STEP WITH A NEW ASSISTANT SESSION

```
Please complete step 1 in @STEPS.md. Refer to the appropriate section in @DESIGN.md to ensure you're meeting all of the acceptance criteria.
```

Don't be satisfied with all green on your test run. Test it manually. Make sure you can see what you expect to see in the traces (responses, errors, tool calls, memory operations, context summaries, etc). Have your assistant create CLI interfaces so you can _verify_ everything is actually working.

**Critical for Module 8:** After implementing ConversationSummaryMemory, test it thoroughly:
- Ask about multiple features in one conversation
- Request multiple large planning documents
- Check traces to confirm summarization occurred
- Verify conversation remains coherent after summarization

#### Remember to: STAGE/COMMIT THE WORKING TREE

After each major step, commit your working code:

```bash
git add .
git commit -m "Step X: [description]"
```

This gives you safe rollback points if needed.

### Step-by-Step Workflow

The recommended progression (detailed in `STEPS.md`):

1. **Step 1: Add Comprehensive Metrics Analysis**
   - Expand analysis tool to support all 5 metrics types
   - Update system prompt with comprehensive decision criteria
   - Verify agent retrieves multiple metrics

2. **Step 2: Add Review Analysis Tools**
   - Add support for 3 review types
   - Update system prompt with review-based decision rules
   - Verify agent blocks on review findings

3. **Step 3: Add Planning Document Tools**
   - Implement list_planning_docs tool
   - Implement read_planning_doc tool
   - Implement search_planning_docs tool (ripgrep)
   - Update system prompt with tool usage guidance
   - Verify intelligent tool selection

4. **Step 4: Implement Context Window Management**
   - Integrate ConversationSummaryMemory
   - Configure summarization thresholds
   - Test with large document scenarios
   - Verify conversation coherence across summaries

5. **Step 5: Update Observability**
   - Add tracing for planning doc tools
   - Track memory operations
   - Log data retrieval volumes
   - Verify trace completeness

6. **Step 6: Update Evaluations**
   - Create Module 8 evaluation scenarios
   - Implement comprehensive retrieval evaluator
   - Implement context management evaluator
   - Run evaluations and achieve >75% pass rate

### Verification Guidelines

For each step:

- ✅ **Run automated tests** - Ensure code quality
- ✅ **Run manual CLI tests** - Verify actual behavior
- ✅ **Check traces** - Ensure observability is capturing everything
- ✅ **Verify context management** - Confirm no overflow or truncation
- ✅ **Test edge cases** - Missing data, errors, large files, multiple features
- ✅ **Check memory operations** - Confirm summarization when expected

Don't move to the next step until the current step is fully working.

### When You're Done

Repeat until Investigator Agent is ready for Module 8 completion:

> _All of the acceptance criteria are met_

The agent should be able to:
- Accept natural language queries about feature readiness
- Retrieve comprehensive data from all sources (metrics, reviews, planning)
- Manage context effectively using ConversationSummaryMemory
- Handle large documents and multi-feature conversations
- Make sound decisions with clear justifications citing multiple sources
- Pass comprehensive evaluations (>75% success rate)

:)

## Tips for Success

1. **Build incrementally** - Each step adds one capability
2. **Verify thoroughly** - Don't skip manual testing, especially for context management
3. **Watch your context** - Use traces to see when summarization occurs
4. **Test with large data** - Actually retrieve multiple large docs to stress test
5. **Use traces** - They show what's really happening with memory and retrieval
6. **Commit often** - Safe rollback points are invaluable
7. **Test multi-turn conversations** - Context management needs multiple turns to demonstrate

## Key Learnings from This Module

By completing this exercise, you'll learn:

- **Context Window Management**: How to prevent context overflow using memory strategies
- **ConversationSummaryMemory**: How LangChain's built-in memory works and when it activates
- **Comprehensive Retrieval**: How to retrieve and synthesize data from multiple sources
- **Tool Selection**: When to use targeted search vs full document reads
- **Large Document Handling**: Techniques for working with data that exceeds context limits
- **Multi-Source Decisions**: How to combine metrics, reviews, and planning docs into coherent assessments
- **Real-world Agent Design**: Practical patterns for production agent systems that handle large data volumes

## Extracurricular: Advanced Retrieval (Optional)

The project includes infrastructure for advanced retrieval capabilities that go beyond the core exercise:

### Vector Database (Chroma)
- **What it is**: Semantic search across planning documentation
- **Setup**: `docker-compose up chroma` + `python scripts/ingest_to_vector_store.py`
- **Use case**: "Find all architecture decisions mentioning authentication"
- **Why optional**: Direct file access + ripgrep achieves similar results with less complexity

### Graph Database (Neo4j)  
- **What it is**: Code AST storage for relationship queries
- **Setup**: `docker-compose up neo4j` + `python scripts/ingest_code_to_neo4j.py`
- **Use case**: "Show all functions modified in Feature X commits"
- **Why optional**: Interesting demonstration, but not essential for readiness assessment

### MCP Servers
- **What they are**: Model Context Protocol servers for standardized tool integration
- **Examples provided**: Chroma MCP, Neo4j MCP, Graphiti MCP
- **Why optional**: Demonstrates standardization but not required for core learning

**Explore these if:**
- You finish the core exercise early
- You want to see semantic search in action
- You're interested in graph-based retrieval
- You want to experiment with MCP protocol

**Documentation:** See `README-ADVANCED.md` for setup instructions

Good luck!
