# Agent Development Guide

## Workflow
- Use the `bd` CLI tool for all task management

## Build/Test Commands
- **Setup**: `uv venv && uv add <package>` (never use pip or requirements.txt)
- **Environment**: `uv sync --all-extras && source .venv/bin/activate`
- **Run CLI**: `python cli.py` (or `python cli.py --eval` for evaluations)
- **All tests**: `pytest src/ tests/ -v`
- **Unit tests only**: `pytest src/ -v`
- **Single test**: `pytest path/to/file_test.py::test_function_name -v`
- **Integration tests**: `pytest tests/integration/ -v`

## Code Style & Conventions
- **Imports**: Use Protocol for interfaces (NOT ABC). Group: stdlib, third-party, local
- **Types**: Full type hints required (Pydantic for data validation, TypedDict for state)
- **Naming**: snake_case for functions/variables, PascalCase for classes
- **Testing**: Unit tests live with code (suffix `_test.py`, NO `test_` prefix). Integration tests in `/tests`
- **Error Handling**: Graceful degradation with retry logic (exponential backoff). Log errors, never suppress
- **DRY**: Never duplicate code without explicit discussion. Ask before violating DRY
- **Quality**: Zero tolerance for failing tests, skipped tests, deprecation warnings, or linting errors

## Project Architecture
- LangChain v1.0.5 + LangGraph v1.0.2 for agentic workflows
- Anthropic Claude (claude-3-5-sonnet-20241022) as LLM
- OpenTelemetry v1.38.0 for observability (traces exported to JSON)
- Configuration via Pydantic Settings + .env files (never use .env directly in code)
