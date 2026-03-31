from src.evaluation.scenarios import create_evaluation_dataset

if __name__ == "__main__":
    print("Refreshing LangSmith dataset for Module 8...")
    dataset_name = create_evaluation_dataset()
    print(f"Dataset '{dataset_name}' refreshed successfully.")
