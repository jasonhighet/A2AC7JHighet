from src.tools.analysis import get_analysis
from src.utils.file_utils import list_available_features

def verify_step1():
    print("Verifying Step 1: Comprehensive Metrics Analysis")
    
    features = list_available_features()
    if not features:
        print("Error: No features found in incoming_data")
        return

    feature_id = features[0]["feature_id"]
    print(f"Testing with Feature ID: {feature_id}")

    metrics_types = [
        "metrics/unit_test_results",
        "metrics/test_coverage_report",
        "metrics/pipeline_results",
        "metrics/performance_benchmarks",
        "metrics/security_scan_results"
    ]

    for m_type in metrics_types:
        print(f"Retrieving {m_type}...")
        result = get_analysis.invoke({
            "feature_id": feature_id,
            "analysis_type": m_type
        })
        
        if "error" in result:
            print(f"  FAILED: {result['error']} - {result.get('message', '')}")
        else:
            print(f"  SUCCESS: Retrieved {len(str(result))} characters of data")
            # Basic content check
            if m_type == "metrics/unit_test_results":
                assert "tests_total" in result
            elif m_type == "metrics/test_coverage_report":
                assert "overall_coverage" in result
            elif m_type == "metrics/pipeline_results":
                assert "recent_runs" in result
            elif m_type == "metrics/performance_benchmarks":
                assert "api_endpoints" in result
            elif m_type == "metrics/security_scan_results":
                assert "vulnerabilities" in result or "overall_risk" in result

    print("\nStep 1 Verification Complete!")

if __name__ == "__main__":
    verify_step1()
