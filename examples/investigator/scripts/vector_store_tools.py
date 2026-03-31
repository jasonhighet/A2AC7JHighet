"""
Vector store tools for querying feature artifacts in ChromaDB.

These tools provide semantic search over planning docs, PRDs, RFCs,
and other feature artifacts stored in the ChromaDB vector store.
"""

import json
import logging
import os
from typing import Any, Optional

import chromadb
from chromadb.config import Settings

from investigator_agent.tools.registry import ToolRegistry

logger = logging.getLogger(__name__)


def _get_chroma_client() -> chromadb.PersistentClient:
    """Get a ChromaDB client connected to the persistent storage."""
    chroma_dir = os.getenv("CHROMA_DATA_DIR", "./data/chromadb")

    # Ensure the directory exists
    os.makedirs(chroma_dir, exist_ok=True)

    client = chromadb.PersistentClient(
        path=chroma_dir,
        settings=Settings(
            anonymized_telemetry=False,
            allow_reset=True,
        ),
    )

    return client


def _get_embedding_function():
    """Get the embedding function for ChromaDB queries."""
    from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set")

    model_name = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
    dimensions = int(os.getenv("EMBEDDING_DIMENSIONS", "384"))

    return OpenAIEmbeddingFunction(
        api_key=api_key,
        model_name=model_name,
        dimensions=dimensions,
    )


async def query_vector_store(
    query: str,
    n_results: int = 5,
    collection_name: Optional[str] = None,
    filter_metadata: Optional[dict[str, Any]] = None,
) -> str:
    """
    Query the vector store for semantically similar feature artifacts.

    This tool performs semantic search over planning documents, PRDs, RFCs,
    and other feature artifacts to find relevant context for the given query.

    Args:
        query: Natural language query describing what you're looking for
        n_results: Number of results to return (default: 5, max: 20)
        collection_name: Optional specific collection to search (default: feature_artifacts)
        filter_metadata: Optional metadata filters (e.g., {"feature_id": "FEAT-123"})

    Returns:
        JSON string containing search results with documents, metadata, and distances

    Examples:
        >>> await query_vector_store("payment processing architecture decisions")
        >>> await query_vector_store("security considerations for user authentication", n_results=3)
        >>> await query_vector_store("API design", filter_metadata={"doc_type": "RFC"})
    """
    try:
        # Limit results to reasonable number
        n_results = min(max(1, n_results), 20)

        # Get ChromaDB client and collection
        client = _get_chroma_client()
        collection_name = collection_name or os.getenv("COLLECTION_NAME", "feature_artifacts")

        try:
            collection = client.get_collection(
                name=collection_name,
                embedding_function=_get_embedding_function(),
            )
        except Exception as e:
            logger.error(f"Failed to get collection '{collection_name}': {e}")
            return json.dumps({
                "error": f"Collection '{collection_name}' not found",
                "available_collections": [c.name for c in client.list_collections()],
            })

        # Perform the query
        where_filter = filter_metadata if filter_metadata else None

        results = collection.query(
            query_texts=[query],
            n_results=n_results,
            where=where_filter,
        )

        # Format results
        formatted_results = {
            "query": query,
            "n_results": len(results.get("documents", [[]])[0]),
            "results": [],
        }

        if results.get("documents") and results["documents"][0]:
            for i in range(len(results["documents"][0])):
                result = {
                    "document": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i] if results.get("metadatas") else {},
                    "distance": results["distances"][0][i] if results.get("distances") else None,
                }
                formatted_results["results"].append(result)

        return json.dumps(formatted_results, indent=2)

    except Exception as e:
        logger.error(f"Error querying vector store: {e}", exc_info=True)
        return json.dumps({"error": str(e)})


async def list_collections() -> str:
    """
    List all available collections in the vector store.

    Returns:
        JSON string with collection names and document counts
    """
    try:
        client = _get_chroma_client()
        collections = client.list_collections()

        result = {
            "collections": [
                {
                    "name": col.name,
                    "count": col.count(),
                }
                for col in collections
            ]
        }

        return json.dumps(result, indent=2)

    except Exception as e:
        logger.error(f"Error listing collections: {e}", exc_info=True)
        return json.dumps({"error": str(e)})


async def get_document_by_id(
    document_id: str,
    collection_name: Optional[str] = None,
) -> str:
    """
    Retrieve a specific document by its ID from the vector store.

    Args:
        document_id: The unique identifier for the document
        collection_name: Optional collection name (default: feature_artifacts)

    Returns:
        JSON string with the document content and metadata
    """
    try:
        client = _get_chroma_client()
        collection_name = collection_name or os.getenv("COLLECTION_NAME", "feature_artifacts")

        try:
            collection = client.get_collection(
                name=collection_name,
                embedding_function=_get_embedding_function(),
            )
        except Exception as e:
            return json.dumps({
                "error": f"Collection '{collection_name}' not found",
                "available_collections": [c.name for c in client.list_collections()],
            })

        # Get the document
        result = collection.get(
            ids=[document_id],
            include=["documents", "metadatas"],
        )

        if not result.get("documents") or not result["documents"]:
            return json.dumps({"error": f"Document '{document_id}' not found"})

        return json.dumps({
            "id": document_id,
            "document": result["documents"][0],
            "metadata": result["metadatas"][0] if result.get("metadatas") else {},
        }, indent=2)

    except Exception as e:
        logger.error(f"Error getting document: {e}", exc_info=True)
        return json.dumps({"error": str(e)})


def register_vector_store_tools(registry: ToolRegistry) -> None:
    """
    Register vector store tools with the agent's tool registry.

    Args:
        registry: The ToolRegistry to register tools into
    """
    registry.register(
        name="query_vector_store",
        description=(
            "Search the vector store for semantically similar feature artifacts "
            "(PRDs, RFCs, planning docs). Use this to find relevant context about "
            "features, architectural decisions, and requirements."
        ),
        parameters={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Natural language query describing what you're looking for",
                },
                "n_results": {
                    "type": "integer",
                    "description": "Number of results to return (default: 5, max: 20)",
                    "default": 5,
                },
                "collection_name": {
                    "type": "string",
                    "description": "Optional collection name (default: feature_artifacts)",
                },
                "filter_metadata": {
                    "type": "object",
                    "description": "Optional metadata filters as key-value pairs",
                },
            },
            "required": ["query"],
        },
        handler=query_vector_store,
    )

    registry.register(
        name="list_vector_collections",
        description="List all available collections in the vector store",
        parameters={
            "type": "object",
            "properties": {},
        },
        handler=list_collections,
    )

    registry.register(
        name="get_document_by_id",
        description="Retrieve a specific document by its ID from the vector store",
        parameters={
            "type": "object",
            "properties": {
                "document_id": {
                    "type": "string",
                    "description": "The unique identifier for the document",
                },
                "collection_name": {
                    "type": "string",
                    "description": "Optional collection name (default: feature_artifacts)",
                },
            },
            "required": ["document_id"],
        },
        handler=get_document_by_id,
    )

    logger.info("Registered 3 vector store tools")
