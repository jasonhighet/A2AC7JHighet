# DevOps Dashboard MCP

A comprehensive example implementation of Model Context Protocol (MCP) servers demonstrating both stdio and HTTP transport patterns. This project simulates a DevOps dashboard that aggregates deployment status, environment health, and release information.

## Overview

This project implements two MCP servers:

- **Stdio MCP Server**: Command-line tools for quick DevOps operations
- **HTTP MCP Server**: REST API endpoints for rich data queries and dashboard integration

## Project Structure

```
devops-dashboard-mcp/
├── README.md                    # This file
├── pyproject.toml              # Python project configuration
├── stdio-server/               # Stdio MCP server implementation
│   ├── main.py                 # Server entry point
│   ├── tools/                  # Individual tool implementations
│   └── __init__.py
├── http-server/                # HTTP MCP server implementation
│   ├── main.py                 # Server entry point
│   ├── routes/                 # API endpoint implementations
│   └── __init__.py
├── data/                       # Mock data files
└── docs/                       # Documentation
```

## Features

### Stdio MCP Server Tools

- `get-deployment-status` - Get current deployment status across environments
- `list-recent-releases` - Show recent version deployments
- `check-environment-health` - Check health status of services
- `promote-release` - Simulate promoting releases between environments

### HTTP MCP Server Endpoints

- `GET /deployments` - Detailed deployment history and current states
- `GET /metrics` - Performance metrics and monitoring data
- `GET /health` - Comprehensive health checks across services
- `GET /logs` - Recent logs and events from deployments

## Getting Started

### Prerequisites

- Python 3.13 or higher
- `uv` package manager (recommended)

### Installation

1. Clone or download this project
2. Install dependencies:
   ```bash
   uv sync
   ```

### Running the Servers

**Stdio MCP Server:**
```bash
uv run devops-stdio-server
```

**HTTP MCP Server:**
```bash
uv run python http-server/main.py
```

## Development

### Testing

Run tests with:
```bash
uv run pytest
```

### Code Formatting

Format code with:
```bash
uv run black .
```

### Type Checking

Check types with:
```bash
uv run mypy .
```

## Educational Purpose

This project serves as a learning example for:

- MCP server implementation patterns
- Stdio vs HTTP transport mechanisms
- Tool and endpoint design
- Data persistence with JSON files
- Testing MCP servers with MCP Inspector and Claude Desktop

## License

This project is for educational purposes.
