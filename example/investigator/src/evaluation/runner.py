"""Evaluation runner using LangSmith SDK.

This module provides functions to run evaluation experiments using LangSmith's
evaluate() function with our custom evaluators.
"""

import os
from typing import Any

from langsmith.evaluation import evaluate

from src.agent.graph import create_agent_graph
from src.evaluation.evaluators import (
    evaluate_decision_quality,
    evaluate_feature_identification,
    evaluate_tool_usage,
)
from src.utils.config import load_config


def run_evaluation(
    dataset_name: str = "investigator-agent-eval",
    experiment_prefix: str = "investigator-eval",
    max_concurrency: int = 2,
) -> dict[str, Any]:
    """Run evaluation using LangSmith's evaluate() function.

    This function:
    1. Loads the agent configuration and creates the agent graph
    2. Defines a target function that wraps the agent for evaluation
    3. Runs LangSmith's evaluate() with our custom evaluators
    4. Returns experiment results including URL for viewing in LangSmith UI

    Args:
        dataset_name: Name of the LangSmith dataset to evaluate against
        experiment_prefix: Prefix for the experiment name (timestamp auto-added)
        max_concurrency: Maximum number of examples to run in parallel

    Returns:
        Experiment results dict with experiment_url and metrics

    Raises:
        ValueError: If LangSmith API key is not configured
    """
    # Load configuration
    config = load_config()

    if not config.langsmith_api_key:
        raise ValueError(
            "LangSmith API key not configured. "
            "Set LANGSMITH_API_KEY in your .env file.\n"
            "Get your API key from: https://smith.langchain.com/settings"
        )

    # Set environment variables that LangSmith expects
    os.environ["LANGSMITH_API_KEY"] = config.langsmith_api_key
    os.environ["LANGSMITH_PROJECT"] = config.langsmith_project

    print(f"\n{'=' * 60}")
    print("RUNNING EVALUATION")
    print(f"{'=' * 60}\n")
    print(f"Dataset: {dataset_name}")
    print(f"Experiment: {experiment_prefix}")
    print(f"Concurrency: {max_concurrency}")
    print(f"LangSmith Project: {config.langsmith_project}")
    print()

    # Create agent graph
    print("Initializing agent...")
    agent = create_agent_graph(config)
    print("✅ Agent initialized\n")

    # Define target function
    def run_agent(inputs: dict) -> dict:
        """Wrapper to run agent on a single evaluation example.

        Args:
            inputs: Input dict with 'user_query' key

        Returns:
            Output dict with 'output' key containing agent's final response
        """
        user_query = inputs["user_query"]

        # Invoke agent
        result = agent.invoke({"messages": [("user", user_query)]})

        # Extract final message content
        final_message = result["messages"][-1]
        output_text = (
            final_message.content
            if hasattr(final_message, "content")
            else str(final_message)
        )

        return {"output": output_text}

    # Run evaluation
    print("Running evaluation...")
    print("(This may take a few minutes depending on dataset size)\n")

    results = evaluate(
        run_agent,  # The agent function to test
        data=dataset_name,  # Dataset in LangSmith
        evaluators=[  # Our custom evaluators
            evaluate_feature_identification,
            evaluate_tool_usage,
            evaluate_decision_quality,
        ],
        experiment_prefix=experiment_prefix,
        max_concurrency=max_concurrency,
        description=f"Evaluation of Investigator Agent on {dataset_name}",
        metadata={
            "model": config.model_name,
            "temperature": config.temperature,
            "step": "6",
        },
    )

    print("\n✅ Evaluation complete!\n")

    return results


def print_evaluation_summary(results: dict[str, Any]) -> None:
    """Print a summary of evaluation results.

    Note: Full analysis should be done in LangSmith UI.
    This is just a quick CLI summary.

    Args:
        results: Experiment results from evaluate()
    """
    print(f"{'=' * 60}")
    print("EVALUATION SUMMARY")
    print(f"{'=' * 60}\n")

    # Print experiment URL
    if "experiment_url" in results:
        print("📊 View detailed results at:")
        print(f"   {results['experiment_url']}\n")

    # Print aggregate stats if available
    if "results" in results:
        total = len(results["results"])
        print(f"Total Examples Evaluated: {total}\n")

    # Instructions for analysis
    print("To analyze results:")
    print("1. Open the URL above in your browser")
    print("2. Review aggregate metrics and pass rates")
    print("3. Drill into failing examples to view full traces")
    print("4. Compare to previous experiments to track progress")
    print("5. Identify patterns in failures to improve the agent\n")

    print(f"{'=' * 60}\n")


def get_experiment_stats(experiment_results: dict[str, Any]) -> dict[str, Any]:
    """Extract statistics from experiment results.

    Args:
        experiment_results: Results from evaluate()

    Returns:
        Dict with aggregate statistics
    """
    if "results" not in experiment_results:
        return {"error": "No results found in experiment"}

    results = experiment_results["results"]
    total = len(results)

    # Count scores for each evaluator
    evaluator_scores: dict[str, list[float]] = {
        "feature_identification": [],
        "tool_usage": [],
        "decision_quality": [],
    }

    for result in results:
        if "evaluation_results" in result:
            for eval_result in result["evaluation_results"]:
                key = eval_result.get("key")
                score = eval_result.get("score")

                if key and score is not None:
                    if key in evaluator_scores:
                        evaluator_scores[key].append(score)

    # Calculate averages
    stats = {
        "total_examples": total,
        "evaluators": {},
    }

    for evaluator, scores in evaluator_scores.items():
        if scores:
            avg_score = sum(scores) / len(scores)
            pass_count = sum(1 for s in scores if s >= 0.7)  # 70% threshold
            pass_rate = (pass_count / len(scores)) * 100

            stats["evaluators"][evaluator] = {
                "avg_score": round(avg_score, 3),
                "pass_rate": round(pass_rate, 1),
                "num_evaluated": len(scores),
            }

    return stats


if __name__ == "__main__":
    # Allow running this module directly for quick evaluation
    import sys

    dataset_name = "investigator-agent-eval"
    if len(sys.argv) > 1:
        dataset_name = sys.argv[1]

    try:
        results = run_evaluation(dataset_name=dataset_name)
        print_evaluation_summary(results)

        # Print stats
        stats = get_experiment_stats(results)
        if "evaluators" in stats:
            print("\nEvaluator Performance:")
            for evaluator, metrics in stats["evaluators"].items():
                print(
                    f"  {evaluator}: {metrics['avg_score']} avg, "
                    f"{metrics['pass_rate']}% pass rate"
                )
            print()

    except ValueError as e:
        print(f"\n❌ Error: {e}\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}\n")
        import traceback

        traceback.print_exc()
        sys.exit(1)
