# Evaluation Module

This module implements LangSmith-based evaluation for the Investigator Agent.

## Structure

- `LANGSMITH_GUIDE.md` - Comprehensive learning guide for LangSmith evaluation concepts
- `scenarios.py` - Test scenario definitions and dataset creation
- `evaluators.py` - Custom evaluator functions for scoring agent performance
- `runner.py` - Evaluation runner using LangSmith SDK
- `*_test.py` - Unit tests for evaluators

## Quick Start

### 1. Set up LangSmith API Key

Add to your `.env` file:
```bash
LANGSMITH_API_KEY=your_api_key_here
LANGSMITH_PROJECT=investigator-agent
```

### 2. Create Evaluation Dataset

```bash
python cli.py --create-dataset
```

This creates a dataset in LangSmith with 8+ test scenarios.

### 3. Run Evaluation

```bash
python cli.py --eval
```

This runs the agent on all test scenarios and generates scores using custom evaluators.

### 4. View Results

Open the experiment URL printed by the CLI to view:
- Aggregate metrics (pass rates, average scores)
- Individual run traces
- Comparison with previous experiments

## Evaluation Dimensions

We evaluate the agent across three dimensions:

1. **Feature Identification Accuracy**: Does the agent correctly identify which feature the user is asking about?
2. **Tool Usage Correctness**: Does the agent call the right tools with correct parameters?
3. **Decision Quality**: Does the agent make the correct readiness decision with proper evidence?

## Test Scenarios

Our dataset includes:

- **Happy Path**: Clear queries with complete data
- **Failing Tests**: Features with test failures that should block progression
- **Ambiguous Queries**: Partial feature names or unclear references
- **Edge Cases**: Missing data, invalid feature names, etc.

## Success Criteria

The agent should achieve:
- **>70% pass rate** on the evaluation dataset
- **100% accuracy** on feature identification for unambiguous queries
- **Correct tool usage** in all scenarios
- **Evidence-based decisions** with specific test metrics cited

## Development Workflow

1. Write new test scenario → Add to `scenarios.py`
2. Run evaluation → `python cli.py --eval`
3. Review failures in LangSmith UI
4. Fix agent issues (prompts, tools, logic)
5. Re-run evaluation to verify improvements
6. Compare experiments in LangSmith UI to track progress

## Notes

- LangSmith handles all infrastructure (storage, metrics, UI)
- We only implement: scenarios, evaluators, integration code
- Focus on unit test and coverage analysis only (Step 6 scope)
- Other analysis types will be added in future steps
