#!/usr/bin/env python3
"""
Vector Store Ingestion Script for Feature Readiness Assessment Agent

This script ingests planning documents from the test data into ChromaDB
for semantic search capabilities. It's designed for a learning environment
to demonstrate RAG (Retrieval Augmented Generation) concepts.

Usage:
    python ingest_to_vector_store.py [--features feature1,feature2] [--verbose]
"""

import os
import re
import json
import argparse
from pathlib import Path
from typing import List, Dict, Tuple
from datetime import datetime, timezone
import chromadb
from chromadb.config import Settings
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
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
EMBEDDING_DIMENSIONS = int(os.getenv("EMBEDDING_DIMENSIONS", "384"))
DATA_DIR = PROJECT_ROOT / "data" / "incoming"


class DocumentChunker:
    """
    Simple document chunker for markdown files.
    Chunks by headers and size limits for better semantic coherence.
    """

    def __init__(self, max_chunk_size: int = 1000, chunk_overlap: int = 100):
        self.max_chunk_size = max_chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_by_headers(self, content: str, file_path: str) -> List[Tuple[str, Dict]]:
        """
        Chunk markdown content by headers for semantic coherence.
        Returns list of (chunk_text, metadata) tuples.
        """
        chunks = []
        lines = content.split('\n')
        current_chunk = []
        current_header = "Introduction"
        current_size = 0

        for line in lines:
            # Detect markdown headers
            header_match = re.match(r'^(#{1,6})\s+(.+)$', line)

            if header_match:
                # Save previous chunk if it exists
                if current_chunk:
                    chunk_text = '\n'.join(current_chunk).strip()
                    if chunk_text:
                        chunks.append((chunk_text, {"section": current_header}))

                # Start new chunk with header
                current_header = header_match.group(2).strip()
                current_chunk = [line]
                current_size = len(line)
            else:
                # Add line to current chunk
                current_chunk.append(line)
                current_size += len(line)

                # If chunk gets too large, split it
                if current_size > self.max_chunk_size:
                    chunk_text = '\n'.join(current_chunk).strip()
                    if chunk_text:
                        chunks.append((chunk_text, {"section": current_header}))

                    # Keep overlap for context
                    overlap_lines = current_chunk[-3:] if len(current_chunk) > 3 else current_chunk
                    current_chunk = overlap_lines
                    current_size = sum(len(line) for line in current_chunk)

        # Add final chunk
        if current_chunk:
            chunk_text = '\n'.join(current_chunk).strip()
            if chunk_text:
                chunks.append((chunk_text, {"section": current_header}))

        return chunks

    def chunk_document(self, content: str, file_path: str) -> List[Tuple[str, Dict]]:
        """Main chunking method that uses header-based chunking."""
        return self.chunk_by_headers(content, file_path)


class VectorStoreIngester:
    """
    Handles ingestion of markdown documents into ChromaDB vector store.
    """

    def __init__(
        self,
        persist_directory: str = CHROMA_DATA_DIR,
        collection_name: str = COLLECTION_NAME
    ):
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        self.chunker = DocumentChunker()
        self.jira_metadata_cache = {}  # Cache for JIRA metadata

        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(anonymized_telemetry=False)
        )

        # Create embedding function (same as used in queries)
        self.embedding_function = OpenAIEmbeddingFunction(
            api_key=OPENAI_API_KEY,
            model_name=EMBEDDING_MODEL,
            dimensions=EMBEDDING_DIMENSIONS,
        )

        # Get or create collection with embedding function
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=self.embedding_function,
            metadata={"description": "Feature planning and documentation artifacts"}
        )

        print(f"✓ ChromaDB initialized at: {persist_directory}")
        print(f"✓ Collection: {collection_name}")
        print(f"✓ Embedding model: {EMBEDDING_MODEL} ({EMBEDDING_DIMENSIONS} dimensions)")

        # Load JIRA metadata for all features
        self._load_jira_metadata()

    def _load_jira_metadata(self) -> None:
        """
        Load JIRA metadata for all features from their JIRA files.
        Caches the metadata for use during ingestion.
        """
        for feature_dir in DATA_DIR.iterdir():
            if not feature_dir.is_dir() or not feature_dir.name.startswith('feature'):
                continue

            folder_name = feature_dir.name
            jira_file = feature_dir / 'jira' / 'feature_issue.json'

            if not jira_file.exists():
                # Create minimal entry for features without JIRA data
                self.jira_metadata_cache[folder_name] = {
                    'jira_key': None,
                    'feature_id': None,
                    'summary': 'Unknown Feature',
                    'status': 'UNKNOWN',
                    'priority': None,
                    'labels': []
                }
                continue

            try:
                with open(jira_file, 'r', encoding='utf-8') as f:
                    jira_data = json.load(f)

                fields = jira_data.get('fields', {})

                # Extract status safely
                status_data = fields.get('status', {})
                status = status_data.get('name', 'UNKNOWN') if isinstance(status_data, dict) else 'UNKNOWN'

                # Extract priority safely
                priority_data = fields.get('priority', {})
                priority = priority_data.get('name') if isinstance(priority_data, dict) else None

                self.jira_metadata_cache[folder_name] = {
                    'jira_key': jira_data.get('key'),
                    'feature_id': fields.get('customfield_10001'),
                    'summary': fields.get('summary', 'Unknown Feature'),
                    'status': status,
                    'priority': priority,
                    'labels': fields.get('labels', [])
                }

                print(f"✓ Loaded JIRA metadata for {folder_name}: {jira_data.get('key')}")

            except Exception as e:
                print(f"⚠️  Warning: Could not load JIRA metadata for {folder_name}: {e}")
                self.jira_metadata_cache[folder_name] = {
                    'jira_key': None,
                    'feature_id': None,
                    'summary': 'Unknown Feature',
                    'status': 'ERROR',
                    'priority': None,
                    'labels': []
                }

    def extract_metadata_from_path(self, file_path: Path) -> Dict[str, str]:
        """
        Extract metadata from file path and enrich with JIRA data.
        Expected structure: data/feature{N}/planning/FILENAME.md
        """
        parts = file_path.parts

        # Extract folder name and stage
        folder_name = None
        stage = "planning"  # Default to planning

        for i, part in enumerate(parts):
            if part.startswith('feature'):
                folder_name = part

            # Detect stage from path
            if part in ['planning', 'code', 'metrics', 'reviews']:
                stage = part

        # Get JIRA metadata from cache
        jira_meta = self.jira_metadata_cache.get(folder_name, {})

        # Extract artifact type from filename
        filename = file_path.stem.lower().replace('_', ' ')

        # Build comprehensive metadata with both folder ID and JIRA data
        return {
            'feature_folder': folder_name or 'unknown',
            'jira_key': jira_meta.get('jira_key'),
            'jira_feature_id': jira_meta.get('feature_id'),
            'feature_name': jira_meta.get('summary', 'Unknown Feature'),
            'jira_status': jira_meta.get('status'),
            'jira_priority': jira_meta.get('priority'),
            'jira_labels': ','.join(jira_meta.get('labels', [])),
            'artifact_type': filename,
            'stage': stage,
            'file_path': str(file_path),
            'file_name': file_path.name
        }

    def get_embedding(self, text: str) -> List[float]:
        """
        Generate embedding using ChromaDB's embedding function.
        This ensures consistency with query-time embeddings.
        """
        # ChromaDB's embedding function expects a list of texts
        embeddings = self.embedding_function([text])
        return embeddings[0]

    def ingest_document(self, file_path: Path) -> int:
        """
        Ingest a single markdown document into the vector store.
        Returns the number of chunks created.
        """
        # Read file content
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"✗ Error reading {file_path}: {e}")
            return 0

        # Skip empty files
        if not content.strip():
            print(f"⊘ Skipping empty file: {file_path}")
            return 0

        # Extract base metadata from path
        base_metadata = self.extract_metadata_from_path(file_path)

        # Chunk the document
        chunks = self.chunker.chunk_document(content, str(file_path))

        if not chunks:
            print(f"⊘ No chunks created from: {file_path}")
            return 0

        # Prepare data for ChromaDB
        documents = []
        metadatas = []
        embeddings = []
        ids = []

        for idx, (chunk_text, chunk_meta) in enumerate(chunks):
            # Create unique ID
            doc_id = f"{base_metadata['feature_folder']}_{base_metadata['artifact_type']}_{idx}"

            # Combine base metadata with chunk metadata
            metadata = {
                **base_metadata,
                **chunk_meta,
                'chunk_index': idx,
                'chunk_count': len(chunks),
                'ingestion_timestamp': datetime.now(timezone.utc).isoformat()
            }

            # Filter out None values - ChromaDB doesn't accept them
            metadata = {k: v for k, v in metadata.items() if v is not None}

            # Generate embedding
            try:
                embedding = self.get_embedding(chunk_text)
            except Exception as e:
                print(f"✗ Error generating embedding for chunk {idx} of {file_path}: {e}")
                continue

            documents.append(chunk_text)
            metadatas.append(metadata)
            embeddings.append(embedding)
            ids.append(doc_id)

        # Add to collection
        try:
            self.collection.add(
                documents=documents,
                metadatas=metadatas,
                embeddings=embeddings,
                ids=ids
            )
            print(f"✓ Ingested {file_path.name}: {len(chunks)} chunks")
            return len(chunks)
        except Exception as e:
            print(f"✗ Error adding to collection: {e}")
            return 0

    def ingest_directory(self, directory: Path, pattern: str = "**/*.md", verbose: bool = False) -> Dict[str, int]:
        """
        Ingest all markdown files from a directory.
        Returns statistics about the ingestion.
        """
        stats = {
            'files_processed': 0,
            'files_skipped': 0,
            'total_chunks': 0,
            'errors': 0
        }

        # Find all markdown files
        markdown_files = list(directory.glob(pattern))

        # Filter out README and structure files
        markdown_files = [
            f for f in markdown_files
            if f.name not in ['README.md', 'FOLDER_STRUCTURE.md', 'MIGRATION_PLAN.md']
        ]

        print(f"\n📁 Found {len(markdown_files)} markdown files to process")
        print("=" * 60)

        for idx, file_path in enumerate(sorted(markdown_files), 1):
            if verbose:
                rel_path = file_path.relative_to(PROJECT_ROOT)
                print(f"\n[{idx}/{len(markdown_files)}] Processing: {rel_path}")

            try:
                chunk_count = self.ingest_document(file_path)

                if chunk_count > 0:
                    stats['files_processed'] += 1
                    stats['total_chunks'] += chunk_count
                    if verbose:
                        print(f"  ✓ Created {chunk_count} chunks")
                else:
                    stats['files_skipped'] += 1
                    if verbose:
                        print("  ⊘ Skipped (no content)")
            except Exception as e:
                stats['errors'] += 1
                print(f"  ✗ Error: {str(e)}")

        return stats

    def print_collection_stats(self):
        """Print statistics about the collection."""
        count = self.collection.count()
        print("\n" + "=" * 60)
        print("📊 Collection Statistics")
        print("=" * 60)
        print(f"Total documents in collection: {count}")

        # Sample a few documents to show what's in there
        if count > 0:
            sample = self.collection.peek(limit=5)
            print("\nSample metadata from collection:")
            for i, metadata in enumerate(sample['metadatas'][:3]):
                print(f"\n  Document {i+1}:")
                print(f"    Feature: {metadata.get('feature_name', 'N/A')}")
                print(f"    JIRA Key: {metadata.get('jira_key', 'N/A')}")
                print(f"    Feature ID: {metadata.get('jira_feature_id', 'N/A')}")
                print(f"    Status: {metadata.get('jira_status', 'N/A')}")
                print(f"    Artifact: {metadata.get('artifact_type', 'N/A')}")
                print(f"    Section: {metadata.get('section', 'N/A')}")

    def reset_collection(self):
        """Delete and recreate the collection (useful for testing)."""
        try:
            self.client.delete_collection(name=self.collection_name)
            print(f"✓ Deleted existing collection: {self.collection_name}")
        except:
            pass

        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"description": "Feature planning and documentation artifacts"}
        )
        print(f"✓ Created fresh collection: {self.collection_name}")


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description='Ingest feature documents into ChromaDB vector store'
    )
    parser.add_argument(
        '--features',
        type=str,
        help='Comma-separated list of features to ingest (e.g., feature1,feature3)'
    )
    parser.add_argument(
        '--verbose',
        '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    parser.add_argument(
        '--reset',
        action='store_true',
        help='Reset the collection before ingesting (non-interactive)'
    )
    parser.add_argument(
        '--no-reset',
        action='store_true',
        help='Do not reset the collection (non-interactive)'
    )

    args = parser.parse_args()

    print("\n" + "=" * 60)
    print("🚀 Feature Artifacts Vector Store Ingestion")
    print("=" * 60)

    # Check for API key
    if not OPENAI_API_KEY:
        print("\n❌ Error: OPENAI_API_KEY not found in environment")
        print("Please create a .env file with your OpenAI API key")
        print("See .env.example for reference")
        return

    # Filter features if specified
    if args.features:
        feature_list = [f.strip() for f in args.features.split(',')]
        print(f"\n📁 Filtering to features: {', '.join(feature_list)}")

    # Initialize ingester
    ingester = VectorStoreIngester()

    # Handle reset logic
    if args.reset:
        ingester.reset_collection()
    elif not args.no_reset:
        # Interactive prompt
        print("\n⚠️  Do you want to reset the collection? (y/n): ", end="")
        response = input().strip().lower()
        if response == 'y':
            ingester.reset_collection()

    # Ingest documents
    print("\n📥 Starting ingestion...")

    if args.features:
        # Ingest specific features
        feature_list = [f.strip() for f in args.features.split(',')]
        all_stats = {
            'files_processed': 0,
            'files_skipped': 0,
            'total_chunks': 0,
            'errors': 0
        }

        for feature in feature_list:
            feature_dir = DATA_DIR / feature
            if not feature_dir.exists():
                print(f"\n⚠️  Feature directory not found: {feature}")
                continue

            print(f"\n📂 Ingesting {feature}...")
            stats = ingester.ingest_directory(feature_dir, verbose=args.verbose)

            # Aggregate stats
            for key in all_stats:
                all_stats[key] += stats[key]

        stats = all_stats
    else:
        # Ingest all features
        stats = ingester.ingest_directory(DATA_DIR, verbose=args.verbose)

    # Print results
    print("\n" + "=" * 60)
    print("✅ Ingestion Complete!")
    print("=" * 60)
    print(f"Files processed: {stats['files_processed']}")
    print(f"Files skipped: {stats['files_skipped']}")
    print(f"Total chunks created: {stats['total_chunks']}")
    print(f"Errors: {stats['errors']}")

    # Show collection stats
    ingester.print_collection_stats()

    print("\n" + "=" * 60)
    print("✨ Vector store is ready for queries!")
    print("=" * 60)


if __name__ == "__main__":
    main()
