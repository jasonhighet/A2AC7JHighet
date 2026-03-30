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
