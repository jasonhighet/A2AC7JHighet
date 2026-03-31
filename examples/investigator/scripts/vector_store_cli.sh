#!/usr/bin/env bash
#
# Vector Store Management CLI
# Provides easy commands to manage the ChromaDB vector store
#

set -e

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
CHROMA_DIR="$PROJECT_ROOT/data/chromadb"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
print_header() {
    echo -e "${BLUE}============================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}============================================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC}  $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC}  $1"
}

# Command: stats
cmd_stats() {
    print_header "📊 Vector Store Statistics"

    if [ ! -d "$CHROMA_DIR" ]; then
        print_error "ChromaDB not found at: $CHROMA_DIR"
        exit 1
    fi

    cd "$PROJECT_ROOT"
    uv run python -c "
import chromadb
from collections import Counter

client = chromadb.PersistentClient(path='./data/chromadb')
collection = client.get_or_create_collection('feature_artifacts')

all_docs = collection.get()
total = len(all_docs['ids'])

print(f'Total chunks: {total}')
print(f'Database location: ./data/chromadb')
print()

# Analyze by feature
features = Counter([m.get('feature_name', 'Unknown') for m in all_docs['metadatas']])
print('Chunks per feature:')
for feature, count in sorted(features.items()):
    print(f'  {feature}: {count}')
print()

# Analyze by artifact type
types = Counter([m.get('artifact_type', 'Unknown') for m in all_docs['metadatas']])
print('Chunks per artifact type:')
for atype, count in sorted(types.items(), key=lambda x: -x[1]):
    print(f'  {atype}: {count}')
"
}

# Command: destroy
cmd_destroy() {
    print_header "🗑️  Destroy Vector Store"

    if [ ! -d "$CHROMA_DIR" ]; then
        print_warning "ChromaDB not found at: $CHROMA_DIR"
        print_info "Nothing to destroy."
        exit 0
    fi

    print_warning "This will permanently delete the vector store at:"
    print_info "$CHROMA_DIR"
    echo
    read -p "Are you sure? (yes/no): " confirm

    if [ "$confirm" = "yes" ]; then
        rm -rf "$CHROMA_DIR"
        print_success "Vector store destroyed"
    else
        print_info "Cancelled"
    fi
}

# Command: reset
cmd_reset() {
    print_header "🔄 Reset Vector Store"

    print_info "This will destroy and recreate the vector store."
    cmd_destroy

    if [ ! -d "$CHROMA_DIR" ]; then
        print_info "Creating new vector store..."
        mkdir -p "$CHROMA_DIR"
        print_success "Vector store created"
    fi
}

# Command: ingest
cmd_ingest() {
    local features="$1"

    print_header "📥 Ingest Documents"

    cd "$PROJECT_ROOT"

    if [ -n "$features" ]; then
        print_info "Ingesting features: $features"
        uv run python scripts/ingest_to_vector_store.py --features "$features"
    else
        print_info "Ingesting all features"
        echo "n" | uv run python scripts/ingest_to_vector_store.py
    fi
}

# Command: query
cmd_query() {
    local query="$1"
    local top_k="${2:-5}"

    if [ -z "$query" ]; then
        print_error "Query text required"
        echo "Usage: $0 query \"your query here\" [top_k]"
        exit 1
    fi

    print_header "🔍 Query Vector Store"
    print_info "Query: $query"
    print_info "Results: $top_k"
    echo

    cd "$PROJECT_ROOT"
    uv run python scripts/query_vector_store.py --query "$query" --top-k "$top_k"
}

# Command: help
cmd_help() {
    cat << EOF
Vector Store Management CLI

Usage: $0 <command> [options]

Commands:
  stats                    Show vector store statistics
  destroy                  Permanently delete the vector store
  reset                    Destroy and recreate empty vector store
  ingest [features]        Ingest documents (optionally filter by feature)
  query "text" [top_k]     Query the vector store
  help                     Show this help message

Examples:
  $0 stats
  $0 ingest
  $0 ingest feature1,feature2
  $0 query "authentication security concerns" 10
  $0 reset
  $0 destroy

Environment:
  PROJECT_ROOT: $PROJECT_ROOT
  CHROMA_DIR: $CHROMA_DIR
EOF
}

# Main command dispatcher
main() {
    local command="${1:-help}"
    shift || true

    case "$command" in
        stats)
            cmd_stats "$@"
            ;;
        destroy)
            cmd_destroy "$@"
            ;;
        reset)
            cmd_reset "$@"
            ;;
        ingest)
            cmd_ingest "$@"
            ;;
        query)
            cmd_query "$@"
            ;;
        help|--help|-h)
            cmd_help
            ;;
        *)
            print_error "Unknown command: $command"
            echo
            cmd_help
            exit 1
            ;;
    esac
}

main "$@"
