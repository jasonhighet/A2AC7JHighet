# Acme DevOps MCP Server

This MCP server provides tools for interacting with the Acme DevOps CLI.

## Available Tools

### Direct Integration Tools (High Performance)
These tools call the CLI logic directly as a Python library.

- `get_deployment_status`: Get deployment status for applications.
- `check_environment_health`: Check health across services and environments.
- `list_recent_releases`: History of version deployments.
- `promote_release`: Simulation of release promotion flows.

### Subprocess Wrapped Tools (CLI Parity)
These tools execute the CLI as a subprocess to ensure identical behavior to the command line.

- `list-releases`: List releases (`devops-cli releases`).
  - Arguments: `app` (string, optional), `limit` (int, optional).
- `check-health`: Check health (`devops-cli health`).
  - Arguments: `env` (string, optional).

## Installation

```powershell
uv add acme-devops-mcp
```

## Running the Server

```powershell
uv run acme-devops-mcp
```

## Environment Variables

- `ACME_DATA_DIR`: (Internal) Set automatically by the server to point to the `acme-devops-cli/data` directory.
