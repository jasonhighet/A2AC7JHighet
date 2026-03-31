from src.tools.analysis import get_analysis
from src.utils.file_utils import list_available_features

def verify_step2():
    print("Verifying Step 2: Add Review Analysis Tools")
    
    features = list_available_features()
    if not features:
        print("Error: No features found in incoming_data")
        return

    feature_id = features[0]["feature_id"]
    print(f"Testing with Feature ID: {feature_id}")

    review_types = [
        "reviews/security",
        "reviews/uat",
        "reviews/stakeholders"
    ]

    for r_type in review_types:
        print(f"Retrieving {r_type}...")
        result = get_analysis.invoke({
            "feature_id": feature_id,
            "analysis_type": r_type
        })
        
        if "error" in result:
            print(f"  FAILED: {result['error']} - {result.get('message', '')}")
        else:
            print(f"  SUCCESS: Retrieved {len(str(result))} characters of data")
            # Basic content check
            if r_type == "reviews/security":
                assert "review_metadata" in result
            elif r_type == "reviews/uat":
                assert "uat_metadata" in result
            elif r_type == "reviews/stakeholders":
                assert "approval_process_metadata" in result

    print("\nStep 2 Verification Complete!")

if __name__ == "__main__":
    verify_step2()
