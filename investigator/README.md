# Investigator Agent

An autonomous agent that evaluates feature readiness (Dev → UAT → Production) by analysing metadata and test metrics.

## Setup

### Prerequisites
- Python 3.13+
- `uv` package manager
- A Google AI Studio (Gemini) API key

### Installation

```bash
# Clone the repository and navigate to the investigator directory
cd investigator

# Create the virtual environment
uv venv

# Dependencies are already recorded in pyproject.toml
# Activate the venv (Windows)
.venv\Scripts\activate

# Copy and configure environment variables
copy .env.example .env
# Edit .env with your actual API keys
```

### Configuration

Copy `.env.example` to `.env` and fill in your credentials:

| Variable | Description | Required |
|---|---|---|
| `GEMINI_API_KEY` | Google AI Studio API key | ✅ |
| `LANGSMITH_API_KEY` | LangSmith API key for tracing | Optional |
| `LANGSMITH_PROJECT` | LangSmith project name | Optional |
| `MODEL_NAME` | Gemini model (default: `gemini-1.5-flash`) | Optional |
| `TEMPERATURE` | Model temperature (default: `0.0`) | Optional |

## Usage

```bash
# Run the interactive CLI
python cli.py

# Create the LangSmith evaluation dataset
python cli.py --create-dataset

# Run the evaluation suite
python cli.py --eval
```

## Testing

```bash
# Run all unit tests
pytest src/ -v

# Run all tests (unit + integration)
pytest src/ tests/ -v
```

## Project Structure

```
investigator/
├── src/
│   ├── agent/          # LangGraph agent workflow
│   ├── tools/          # JIRA and analysis tools
│   ├── observability/  # OpenTelemetry tracing
│   ├── utils/          # Config and file utilities
│   └── evaluation/     # LangSmith evaluation suite
├── tests/              # Integration tests
├── traces/             # Generated trace JSON files
├── data/               # Conversation persistence and incoming data
└── cli.py              # Entry point
```
