import subprocess
import json
from src.tools.planning import list_planning_docs, read_planning_doc, search_planning_docs
from src.utils.file_utils import list_available_features

def verify_step3():
    print("Verifying Step 3: Add Planning Document Tools")
    
    features = list_available_features()
    if not features:
        print("Error: No features found in incoming_data")
        return

    feature_id = features[0]["feature_id"]
    print(f"Testing with Feature ID: {feature_id}")

    # 1. Test list_planning_docs
    print("Checking list_planning_docs...")
    docs = list_planning_docs.invoke({"feature_id": feature_id})
    print(f"  Available docs: {docs}")
    assert len(docs) > 0
    assert "USER_STORY.md" in docs

    # 2. Test read_planning_doc
    print("Checking read_planning_doc (USER_STORY.md)...")
    content = read_planning_doc.invoke({
        "feature_id": feature_id, 
        "doc_name": "USER_STORY.md"
    })
    print(f"  Retrieved {len(content)} characters.")
    assert "User Story" in content

    # 3. Test search_planning_docs
    print("Checking search_planning_docs (query: 'Acceptance')...")
    # Ensure rg is in PATH or use absolute path
    # For this test, we assume 'rg' is in the PATH as per user instructions
    matches = search_planning_docs.invoke({
        "feature_id": feature_id,
        "query": "Acceptance"
    })
    
    if isinstance(matches, list) and len(matches) > 0 and "text" in matches[0]:
        print(f"  Found {len(matches)} matches.")
        for m in matches[:2]:
            print(f"    {m['file']}:{m['line']} - {m['text']}")
    else:
        print(f"  FAILED or No matches: {matches}")
        # Fallback check if rg is missing from path
        try:
            subprocess.run(["rg", "--version"], capture_output=True, check=True)
        except FileNotFoundError:
            print("  CRITICAL: 'rg' (ripgrep) is not in the system PATH. Please add it.")

    print("\nStep 3 Verification Complete!")

if __name__ == "__main__":
    verify_step3()
