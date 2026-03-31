# Dockerfile for running chroma-mcp server in SSE mode
FROM python:3.12-slim

# Install system dependencies (curl for healthcheck)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Set working directory
WORKDIR /app

# Copy the SSE server script
COPY chroma_mcp_sse_server.py /app/server.py

# Install chroma-mcp and dependencies
RUN uv pip install --system chroma-mcp python-dotenv

# Create data directory
RUN mkdir -p /data/chromadb

# Expose SSE port
EXPOSE 8001

# Set default environment variables
ENV CHROMA_CLIENT_TYPE=persistent
ENV CHROMA_DATA_DIR=/data/chromadb
ENV CHROMA_MCP_HOST=0.0.0.0
ENV CHROMA_MCP_PORT=8001

# Run the SSE server
CMD ["python", "server.py"]
