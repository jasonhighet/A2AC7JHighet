#!/bin/bash

# Neo4j Code AST Management CLI
# Wrapper script for Neo4j code ingestion and querying

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Activate virtual environment
if [ -d "$PROJECT_ROOT/.venv" ]; then
    source "$PROJECT_ROOT/.venv/bin/activate"
else
    echo "❌ Virtual environment not found at $PROJECT_ROOT/.venv"
    echo "Please run 'uv sync' first"
    exit 1
fi

# Display help if no arguments
if [ $# -eq 0 ]; then
    echo "Neo4j Code AST Management CLI"
    echo ""
    echo "Usage:"
    echo "  $0 ingest [options]     - Ingest code diffs into Neo4j"
    echo "  $0 query [query_type]   - Query the Neo4j database"
    echo "  $0 reset                - Reset the database and re-ingest"
    echo ""
    echo "Ingest options:"
    echo "  --features feature1,feature2"
    echo "  --verbose"
    echo "  --reset"
    echo ""
    echo "Query types:"
    echo "  stats, features, functions, files, commits,"
    echo "  complexity, languages, analysis, all"
    echo ""
    echo "Examples:"
    echo "  $0 ingest --reset"
    echo "  $0 ingest --features feature1 --verbose"
    echo "  $0 query stats"
    echo "  $0 query functions --feature feature1"
    exit 0
fi

COMMAND=$1
shift

case "$COMMAND" in
    ingest)
        python "$SCRIPT_DIR/ingest_code_to_neo4j.py" "$@"
        ;;
    query)
        python "$SCRIPT_DIR/query_neo4j_code.py" "$@"
        ;;
    reset)
        python "$SCRIPT_DIR/ingest_code_to_neo4j.py" --reset
        ;;
    *)
        echo "Unknown command: $COMMAND"
        echo "Use: $0 (without args) to see help"
        exit 1
        ;;
esac
