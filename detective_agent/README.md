# Detective Agent

The Detective Agent is an autonomous AI agent designed to investigate software releases, analyze changes, and assess risks.

## Features

- **Autonomous Investigation**: Automatically chains tool calls to gather release data and file risk reports.
- **Observability**: Fully instrumented with OpenTelemetry for tracing LLM calls and tool execution.
- **Context Management**: Intelligent sliding window strategy using `tiktoken` to handle long conversations.
- **Resilience**: Built-in retry mechanism with exponential backoff and jitter for stable LLM connectivity.
- **Evaluation System**: Integrated framework for benchmarking agent accuracy and tool usage.

## Architecture

- `agent.py`: Core agent logic and tool execution loop.
- `provider.py`: Interface for LLM providers (currently supports LLMStudio/OpenAI).
- `models.py`: Pydantic models for structured data and evaluation.
- `tools.py`: Registry for tools available to the agent.
- `context.py`: Token counting and message truncation logic.
- `observability.py`: OpenTelemetry setup and JSON-based tracing.

## Getting Started

1. **Prerequisites**:
   - Python 3.12+
   - `uv` package manager
   - LLMStudio (or compatible OpenAI API) running locally.

2. **Installation**:
   ```powershell
   uv sync
   ```

3. **Configuration**:
   Copy `.env.example` to `.env` and set your variables:
   - `DETECTIVE_LLM_BASE_URL`: Base URL for your LLM (default: http://localhost:1234/v1)
   - `DETECTIVE_MAX_CONTEXT_TOKENS`: Context window limit (default: 4096)

4. **Running the Agent**:
   ```powershell
   uv run python -m detective_agent.cli
   ```

5. **Running Evaluations**:
   ```powershell
   uv run python -m detective_agent.eval_runner
   ```

## Development

### Running Tests
```powershell
uv run pytest detective_agent/
```

### Viewing Traces
Traces are saved as JSON files in the `.traces/` directory. Each trace corresponds to an agent interaction.
