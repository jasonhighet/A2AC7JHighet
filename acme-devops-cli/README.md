# DevOps CLI Tool

A standalone command-line interface for DevOps operations, providing deployment status, release management, environment health monitoring, and release promotion capabilities.

## Overview

The DevOps CLI tool is part of a larger enterprise architecture that demonstrates how to create reusable CLI tools that can be wrapped by various interfaces (MCP servers, HTTP APIs, etc.). This tool provides direct access to DevOps data and operations through a clean command-line interface.

## Architecture

```
acme-devops-cli/
├── devops-cli              # Main executable script
├── lib/                    # Python library modules
│   ├── __init__.py
│   ├── cli_utils.py        # Common utilities and helpers
│   ├── config.py           # Configuration and constants
│   └── commands/           # Individual command implementations
│       └── __init__.py
└── README.md               # This file
```

## Installation

1. Ensure Python 3.8+ is installed on your system
2. Make the main script executable:
   ```bash
   chmod +x devops-cli
   ```
3. Ensure the shared data directory is available at `../acme-devops-shared/data/`

## Usage

### Basic Syntax

```bash
./devops-cli <command> [options]
```

### Global Options

- `--help, -h`: Show help information
- `--version, -v`: Show version information
- `--format`: Output format (json, table) - default: json
- `--verbose`: Enable verbose output

### Available Commands

#### 1. Deployment Status (`status`)

Get deployment status information with optional filtering.

```bash
# Get all deployments
./devops-cli status

# Filter by application
./devops-cli status --app web-app

# Filter by environment
./devops-cli status --env prod

# Both filters with table output
./devops-cli status --app api-service --env staging --format table
```

**Options:**
- `--app, -a <application>`: Filter by application ID
- `--env, -e <environment>`: Filter by environment
- `--format, -f <format>`: Output format (json, table)

#### 2. Recent Releases (`releases`)

List recent releases with optional filtering and limits.

```bash
# Get recent releases (default limit: 10)
./devops-cli releases

# Limit number of results
./devops-cli releases --limit 5

# Filter by application
./devops-cli releases --app web-app

# Table format
./devops-cli releases --format table
```

**Options:**
- `--limit, -l <number>`: Maximum number of releases to return
- `--app, -a <application>`: Filter by application ID
- `--format, -f <format>`: Output format (json, table)

#### 3. Environment Health (`health`)

Check environment health status across applications.

```bash
# Get all environment health data
./devops-cli health

# Filter by environment
./devops-cli health --env prod

# Filter by application
./devops-cli health --app web-app

# Both filters
./devops-cli health --env staging --app api-service
```

**Options:**
- `--env, -e <environment>`: Filter by environment
- `--app, -a <application>`: Filter by application ID
- `--format, -f <format>`: Output format (json, table)

#### 4. Release Promotion (`promote`)

Promote a release from one environment to another.

```bash
# Promote a release
./devops-cli promote --release v1.2.3 --from staging --to prod

# Promote with application specification
./devops-cli promote --release v2.1.0 --from uat --to prod --app web-app
```

**Options:**
- `--release, -r <version>`: Release version to promote (required)
- `--from, -f <environment>`: Source environment (required)
- `--to, -t <environment>`: Target environment (required)
- `--app, -a <application>`: Application ID (optional)

## Output Formats

### JSON Format (Default)

All commands return structured JSON responses with the following format:

```json
{
  "status": "success",
  "message": "Operation completed successfully",
  "data": [...],
  "timestamp": "2024-01-15T10:30:00Z",
  "filters_applied": {
    "application": "web-app",
    "environment": "prod"
  }
}
```

### Table Format

Human-readable table format for terminal display:

```
APPLICATION     ENVIRONMENT          VERSION      STATUS          DEPLOYED_AT          DEPLOYED_BY         
--------------------------------------------------------------------------------------------------------
web-app         prod                 v2.1.3       deployed        2024-01-15 10:30    alice@company.com   
api-service     prod                 v1.8.2       deployed        2024-01-14 09:15    charlie@company.com 
```

## Configuration

### Environment Variables

The CLI tool supports configuration through environment variables:

- `DEVOPS_CLI_DATA_PATH`: Override the default data directory path
- `DEVOPS_CLI_DEFAULT_FORMAT`: Set default output format (json, table)
- `DEVOPS_CLI_TIMEOUT`: Set default timeout for operations (seconds)

### Data Sources

The CLI tool reads data from JSON files in the shared data directory:

- `deployments.json`: Deployment status information
- `releases.json`: Release history and metadata
- `environments.json`: Environment configuration and health data
- `config.json`: Application and system configuration
- `logs.json`: System and application logs
- `metrics.json`: Performance and monitoring metrics
- `release_health.json`: Release health and quality metrics

## Error Handling

The CLI tool provides structured error responses and appropriate exit codes:

- `0`: Success
- `1`: General error
- `2`: Invalid arguments
- `3`: Data error
- `4`: Permission error
- `5`: Timeout error

Error responses follow this format:

```json
{
  "status": "error",
  "error_code": "DATA_ERROR",
  "error_message": "Failed to load deployment data",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## Integration

This CLI tool is designed to be wrapped by other interfaces:

- **MCP Servers**: The `acme-devops-mcp` package wraps this CLI for Model Context Protocol integration
- **HTTP APIs**: Can be wrapped by web services for REST API access
- **Automation Scripts**: Can be called directly from CI/CD pipelines and automation workflows

## Development

### Project Structure

The CLI follows a modular architecture:

- `devops-cli`: Main executable that routes commands
- `lib/cli_utils.py`: Common utilities and formatting functions
- `lib/config.py`: Configuration management and constants
- `lib/commands/`: Individual command implementations (to be added in Phase 2)

### Adding New Commands

1. Create a new module in `lib/commands/`
2. Implement the command logic with proper argument parsing
3. Add the command to the main routing in `devops-cli`
4. Update configuration in `lib/config.py`

## Examples

### Basic Usage Examples

```bash
# Check deployment status for production web-app
./devops-cli status --app web-app --env prod --format table

# Get last 5 releases in JSON format
./devops-cli releases --limit 5

# Check health of all staging environments
./devops-cli health --env staging

# Promote web-app v2.1.0 from staging to production
./devops-cli promote --release v2.1.0 --from staging --to prod --app web-app
```

### Automation Examples

```bash
# Check if production deployments are healthy (exit code indicates status)
if ./devops-cli health --env prod > /dev/null 2>&1; then
    echo "Production is healthy"
else
    echo "Production has issues"
fi

# Get deployment status and parse with jq
./devops-cli status --app web-app | jq '.data[] | select(.environment == "prod")'
```

## Support

For issues, questions, or contributions, please refer to the main project documentation or contact the DevOps team.

---

**Version**: 1.0.0  
**Last Updated**: 2024-01-15  
**Part of**: acme-devops enterprise toolchain
