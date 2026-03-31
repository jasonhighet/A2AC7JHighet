from src.evaluation.runner import run_evaluation, get_experiment_stats
import json

if __name__ == "__main__":
    print("Starting Module 8 Evaluation...")
    # Using max_concurrency=1 for local stability on Windows
    results = run_evaluation(max_concurrency=1)
    
    # Process results - results is an ExperimentResults object which is iterable
    stats = get_experiment_stats(results)
    print("\n--- Evaluation Summary ---")
    print(json.dumps(stats, indent=2))
    
    pass_rate = stats.get("tool_usage", 0) * 100
    print(f"\nFinal Tool Usage Pass Rate: {pass_rate}%")
    
    if pass_rate >= 75:
        print("\nSUCCESS: Module 8 retrieval requirements met (>75% pass rate).")
    else:
        print("\nWARNING: Module 8 retrieval requirements not fully met (<75% pass rate).")
