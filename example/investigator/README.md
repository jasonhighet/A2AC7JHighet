# Investigator Agent

An intelligent agent that assesses software feature readiness for phase progression (Development → UAT → Production) by analyzing feature metadata and test metrics.

## Overview

The Investigator Agent serves as an automated assessor for the CommunityShare platform, helping product managers and engineering teams make informed decisions about feature readiness by analyzing:

- Feature metadata (JIRA tickets, status, context)  
- Test metrics (unit tests, coverage, failures)
- Risk factors and blockers

## Quick Start

### Prerequisites

- Python 3.14+
- uv package manager

### Setup

1. **Clone and setup the project:**
   ```bash
   cd investigator
   uv venv
   source .venv/bin/activate
   ```

2. **Install dependencies:**
   ```bash
   uv sync
   ```

3. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env and add your ANTHROPIC_API_KEY
   ```

4. **Run the CLI:**
   ```bash
   python cli.py
   ```

## Usage

### Example Conversations

**Check feature readiness:**
```
You: Is the reservation feature ready for its next phase?

Agent: I found the reservation feature (FEAT-MS-001) currently in Development status.

✅ **READY FOR UAT** - Feature meets criteria for User Acceptance Testing.

**Analysis:**
- All 156 unit tests passing (100% success rate)
- Code review completed and PR merged
- Security review shows LOW risk
- All stakeholder approvals obtained

**Recommendation:** Move to UAT environment for user testing.
```

**Handle failing tests:**
```
You: Is the QR code check-in feature ready for production?

Agent: I found the QR code check-in feature (FEAT-QR-002) currently in UAT status.

❌ **NOT READY FOR PRODUCTION** - Critical issues prevent production deployment.

**Key Blockers:**
- 2 failed tests including HIGH severity race condition
- Critical bug: Multiple users can check in with same QR code simultaneously
- Second issue with timezone handling in QR expiry logic

**Recommendation:** Fix race condition and timezone bugs before production deployment.
```

## Project Structure

```
investigator/
├── src/
│   ├── agent/          # LangGraph agent workflow
│   ├── tools/          # Feature lookup and analysis tools
│   ├── observability/ # OpenTelemetry tracing
│   ├── utils/          # Configuration and utilities
│   └── evaluation/     # Automated testing framework
├── tests/
│   ├── integration/    # End-to-end tests
│   └── fixtures/       # Test data
├── traces/             # Generated trace JSON files
├── data/incoming/      # Feature test data
├── cli.py              # CLI interface
└── pyproject.toml      # Project configuration
```

## Development

### Running Tests

```bash
# All tests
pytest src/ tests/ -v

# Unit tests only
pytest src/ -v

# Integration tests only
pytest tests/integration/ -v

# Single test
pytest path/to/file_test.py::test_function_name -v
```

### Running Evaluations

```bash
# Run full evaluation suite
python cli.py --eval

# Save baseline for comparison
python cli.py --eval --save-baseline

# Compare to baseline
python cli.py --eval --compare-baseline baseline.json
```

### Environment Variables

- `ANTHROPIC_API_KEY`: Your Anthropic API key (required)
- `MODEL_NAME`: Claude model to use (default: claude-3-5-sonnet-20241022)
- `TEMPERATURE`: Model temperature (default: 0.0)
- `MAX_TOKENS`: Maximum tokens per response (default: 4096)
- `TRACE_OUTPUT_DIR`: Directory for trace files (default: traces/)

## Architecture

Built with:
- **LangChain 1.0.5** - Core framework
- **LangGraph 1.0.2** - Agent orchestration  
- **Anthropic Claude** - Language model
- **OpenTelemetry** - Observability and tracing
- **Pydantic** - Data validation and configuration
- **pytest** - Testing framework

## Contributing

1. Follow the project structure defined in `PLAN.md`
2. Write tests for all new functionality
3. Ensure all tests pass before committing
4. Use type hints and proper documentation

## License

[Add your license here]
