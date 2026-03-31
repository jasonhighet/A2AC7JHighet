#!/usr/bin/env python3
"""
Simple query interface for the vector store.

This script allows you to test semantic search queries against the
ingested feature documentation.

Usage:
    python query_vector_store.py                          # Interactive mode
    python query_vector_store.py --query "your query"     # Single query
    python query_vector_store.py --query "..." --top-k 10  # More results
"""

import os
import argparse
from pathlib import Path
from openai import OpenAI
import chromadb
from chromadb.config import Settings
from dotenv import load_dotenv

# Get the project root directory (parent of scripts directory)
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent

# Load environment variables from project root
load_dotenv(PROJECT_ROOT / ".env")

# Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
CHROMA_DATA_DIR = os.getenv("CHROMA_DATA_DIR", str(PROJECT_ROOT / "data" / "chromadb"))
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "feature_artifacts")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

# Initialize OpenAI client
openai_client = OpenAI(api_key=OPENAI_API_KEY)


def get_embedding(text: str):
    """Generate embedding for query text."""
    response = openai_client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=text
    )
    return response.data[0].embedding


def query_vector_store(query: str, n_results: int = 5, feature_filter: str = None):
    """
    Query the vector store with semantic search.

    Args:
        query: Natural language query
        n_results: Number of results to return
        feature_filter: Optional feature_id to filter results
    """
    # Initialize ChromaDB
    client = chromadb.PersistentClient(
        path=CHROMA_DATA_DIR,
        settings=Settings(anonymized_telemetry=False)
    )

    # Get collection
    try:
        collection = client.get_collection(name=COLLECTION_NAME)
    except Exception as e:
        print(f"❌ Error: Collection '{COLLECTION_NAME}' not found")
        print("Please run ingest_to_vector_store.py first")
        return

    # Generate query embedding
    query_embedding = get_embedding(query)

    # Build filter if needed
    where_filter = None
    if feature_filter:
        where_filter = {"feature_id": feature_filter}

    # Query the collection
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
        where=where_filter
    )

    # Display results
    print("\n" + "=" * 80)
    print(f"🔍 Query: {query}")
    if feature_filter:
        print(f"📌 Filter: {feature_filter}")
    print("=" * 80)

    if not results['documents'][0]:
        print("\n❌ No results found")
        return

    for i, (doc, metadata, distance) in enumerate(zip(
        results['documents'][0],
        results['metadatas'][0],
        results['distances'][0]
    )):
        print(f"\n--- Result {i+1} (similarity: {1 - distance:.3f}) ---")
        print(f"Feature: {metadata.get('feature_name', 'N/A')}")
        print(f"Artifact: {metadata.get('artifact_type', 'N/A')}")
        print(f"Section: {metadata.get('section', 'N/A')}")
        print(f"File: {metadata.get('file_name', 'N/A')}")
        print("\nContent Preview:")
        preview = doc[:300] + "..." if len(doc) > 300 else doc
        print(preview)

    print("\n" + "=" * 80)


def interactive_mode():
    """Run interactive query mode."""
    print("\n" + "=" * 80)
    print("🔍 Interactive Vector Store Query")
    print("=" * 80)
    print("\nAvailable features:")
    print("  - feature1: Maintenance Scheduling & Alert System")
    print("  - feature2: QR Code Check-in/out with Mobile App")
    print("  - feature3: Advanced Resource Reservation System")
    print("  - feature4: Contribution Tracking & Community Credits")
    print("\nCommands:")
    print("  - Type your query to search")
    print("  - Type 'filter:feature1' before query to filter by feature")
    print("  - Type 'quit' to exit")
    print("=" * 80)

    feature_filter = None

    while True:
        print("\n> ", end="")
        user_input = input().strip()

        if user_input.lower() in ['quit', 'exit', 'q']:
            print("👋 Goodbye!")
            break

        # Check for filter command
        if user_input.startswith('filter:'):
            feature_filter = user_input.split(':', 1)[1].strip()
            print(f"✓ Filter set to: {feature_filter}")
            print("  (Type 'filter:' to clear)")
            continue
        elif user_input == 'filter:':
            feature_filter = None
            print("✓ Filter cleared")
            continue

        if not user_input:
            continue

        # Execute query
        try:
            query_vector_store(user_input, n_results=3, feature_filter=feature_filter)
        except Exception as e:
            print(f"❌ Error: {e}")


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description='Query the vector store with semantic search'
    )
    parser.add_argument(
        '--query',
        '-q',
        type=str,
        help='Query text to search for'
    )
    parser.add_argument(
        '--top-k',
        '-k',
        type=int,
        default=5,
        help='Number of results to return (default: 5)'
    )
    parser.add_argument(
        '--feature',
        '-f',
        type=str,
        help='Filter by feature (e.g., feature1, feature2)'
    )

    args = parser.parse_args()

    # Check for API key
    if not OPENAI_API_KEY:
        print("\n❌ Error: OPENAI_API_KEY not found in environment")
        print("Please create a .env file with your OpenAI API key")
        return

    # Single query mode
    if args.query:
        query_vector_store(args.query, n_results=args.top_k, feature_filter=args.feature)
        return

    # Interactive mode
    # Example queries
    example_queries = [
        "What are the acceptance criteria for the maintenance feature?",
        "Show me architecture decisions about authentication",
        "What deployment steps are required?",
    ]

    print("\n💡 Example queries:")
    for i, q in enumerate(example_queries, 1):
        print(f"  {i}. {q}")

    # Start interactive mode
    interactive_mode()


if __name__ == "__main__":
    main()
