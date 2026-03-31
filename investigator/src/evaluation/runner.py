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
    max_concurrency: int = 1,
) -> dict[str, Any]:
    """Run evaluation using LangSmith's evaluate() function."""
    config = load_config()

    if not config.langsmith_api_key:
        raise ValueError("LangSmith API key not configured in .env.")

    os.environ["LANGSMITH_API_KEY"] = config.langsmith_api_key
    os.environ["LANGSMITH_PROJECT"] = config.langsmith_project

    agent = create_agent_graph(config)

    def run_agent(inputs: dict) -> dict:
        """Invokes the agent graph."""
        user_query = inputs["user_query"]
        # Initialize state with empty summary for each fresh evaluation run
        result = agent.invoke({"messages": [("user", user_query)], "summary": ""})
        final_message = result["messages"][-1]
        output_text = final_message.content if hasattr(final_message, "content") else str(final_message)
        return {"output": output_text}

    print(f"Running evaluation on '{dataset_name}'...")
    results = evaluate(
        run_agent,
        data=dataset_name,
        evaluators=[
            evaluate_feature_identification,
            evaluate_tool_usage,
            evaluate_decision_quality,
        ],
        experiment_prefix=experiment_prefix,
        max_concurrency=max_concurrency,
        description=f"Evaluation of Investigator Agent on {dataset_name}",
        metadata={"model": config.model_name, "step": "6"},
    )

    return results


def get_experiment_stats(experiment_results: Any) -> dict[str, Any]:
    """Calculate aggregate stats for different evaluators."""
    stats: dict[str, dict] = {}
    
    # Force evaluation into a list to ensure all rows are processed
    try:
        rows = list(experiment_results)
    except Exception as e:
        print(f"DEBUG: Error converting experiment_results to list: {e}")
        return {}

    for row in rows:
        eval_data = row.get("evaluation_results", {})
        
        # LangSmith results are typically in a 'results' list within evaluation_results
        results_list = []
        if isinstance(eval_data, dict):
            if "results" in eval_data:
                results_list = eval_data["results"]
            else:
                # Fallback to values if formatted differently
                results_list = list(eval_data.values())
        elif isinstance(eval_data, list):
            results_list = eval_data

        for res in results_list:
            # Extract key and score. res is typically an EvaluationResult object.
            if hasattr(res, "key") and hasattr(res, "score"):
                key = res.key
                score = res.score
            elif isinstance(res, dict):
                key = res.get("key")
                score = res.get("score")
            else:
                continue
                
            if key and score is not None:
                if key not in stats:
                    stats[key] = {"total_score": 0, "count": 0}
                stats[key]["total_score"] += score
                stats[key]["count"] += 1

    summary = {}
    for key, data in stats.items():
        summary[key] = round(data["total_score"] / data["count"], 2) if data["count"] > 0 else 0

    return summary
