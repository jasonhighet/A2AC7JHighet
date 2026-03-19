# DevOps Dashboard API

A standalone REST API for DevOps dashboard functionality, providing endpoints for deployments, metrics, health checks, and logs. This API serves as the backend for DevOps operations and can be consumed by MCP servers, web applications, or any HTTP client.

## Features

- **FastAPI Framework**: Modern, fast, and well-documented API with automatic OpenAPI documentation
- **Standalone Architecture**: Self-contained with its own data files and business logic
- **RESTful Design**: Clean REST endpoints with consistent response formats
- **Comprehensive Testing**: Full test coverage with pytest and FastAPI test client
- **Error Handling**: Standardized error responses and logging
- **CORS Support**: Cross-origin resource sharing for web applications
- **Auto Documentation**: Interactive API docs at `/docs` and `/redoc`

## Quick Start

### Prerequisites

- Python 3.11+
- UV package manager (recommended) or pip

### Installation

1. **Clone and navigate to the API directory:**
   ```bash
   cd acme-devops-api
   ```

2. **Install dependencies with UV:**
   ```bash
   uv sync
   ```

   Or with pip:
   ```bash
   pip install -e .
   ```

3. **Start the API server:**
   ```bash
   ./api-server
   ```

   Or directly with Python:
   ```bash
   python app.py
   ```

4. **Access the API:**
   - API Base URL: http://localhost:8000
   - Interactive Docs: http://localhost:8000/docs
   - ReDoc Documentation: http://localhost:8000/redoc
   - Health Check: http://localhost:8000/health

## API Endpoints

### Base Information

- **GET /** - API information and available endpoints
- **GET /health** - Simple health check for load balancers

### DevOps Operations (v1)

All DevOps endpoints are prefixed with `/api/v1`:

#### Deployments
- **GET /api/v1/deployments** - Get deployment data with filtering and pagination
  - Query Parameters:
    - `application` (string): Filter by application ID
    - `environment` (string): Filter by environment
    - `limit` (integer): Maximum results to return
    - `offset` (integer): Pagination offset

#### Metrics
- **GET /api/v1/metrics** - Get performance metrics with aggregations
  - Query Parameters:
    - `application` (string): Filter by application ID
    - `environment` (string): Filter by environment
    - `time_range` (string): Time range for metrics

#### Health Checks
- **GET /api/v1/health** - Get health status across services
  - Query Parameters:
    - `environment` (string): Filter by environment
    - `application` (string): Filter by application
    - `detailed` (boolean): Include detailed health information

#### Logs
- **GET /api/v1/logs** - Get log entries with filtering
  - Query Parameters:
    - `application` (string): Filter by application ID
    - `environment` (string): Filter by environment
    - `level` (string): Filter by log level
    - `limit` (integer): Maximum results to return

## Usage Examples

### Using curl

```bash
# Get all deployments
curl http://localhost:8000/api/v1/deployments

# Get deployments for specific application
curl "http://localhost:8000/api/v1/deployments?application=web-app"

# Get deployments with pagination
curl "http://localhost:8000/api/v1/deployments?limit=10&offset=0"

# Get health status
curl http://localhost:8000/api/v1/health

# Get metrics for production environment
curl "http://localhost:8000/api/v1/metrics?environment=prod"
```

### Using Python requests

```python
import requests

# Get deployments
response = requests.get("http://localhost:8000/api/v1/deployments")
data = response.json()

# Filter deployments
response = requests.get(
    "http://localhost:8000/api/v1/deployments",
    params={"application": "web-app", "environment": "prod"}
)
```

### Using httpx (async)

```python
import httpx

async def get_deployments():
    async with httpx.AsyncClient() as client:
        response = await client.get("http://localhost:8000/api/v1/deployments")
        return response.json()
```

## Response Format

All API responses follow a consistent format:

### Success Response
```json
{
  "status": "success",
  "data": {
    // Response data here
  },
  "timestamp": "2024-01-15T10:30:00Z",
  "metadata": {
    // Optional metadata
  }
}
```

### Error Response
```json
{
  "status": "error",
  "message": "Error description",
  "error_code": "ERROR_CODE",
  "timestamp": "2024-01-15T10:30:00Z",
  "details": {
    // Optional error details
  }
}
```

### Paginated Response
```json
{
  "status": "success",
  "data": {
    "items": [
      // Array of items
    ],
    "pagination": {
      "total": 100,
      "returned": 10,
      "limit": 10,
      "offset": 0,
      "has_more": true
    }
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## Configuration

### Environment Variables

- `HOST` - Server host (default: 127.0.0.1)
- `PORT` - Server port (default: 8000)
- `WORKERS` - Number of worker processes (default: 1)

### Example

```bash
export HOST=0.0.0.0
export PORT=8080
export WORKERS=4
./api-server
```

## Development

### Project Structure

```
acme-devops-api/
├── api-server              # Main executable script
├── app.py                  # FastAPI application
├── pyproject.toml         # UV project configuration
├── data/                  # JSON data files
│   ├── config.json
│   ├── deployments.json
│   ├── environments.json
│   ├── logs.json
│   ├── metrics.json
│   ├── release_health.json
│   └── releases.json
├── lib/                   # Shared utilities
│   ├── __init__.py
│   ├── data_loader.py     # Data loading utilities
│   ├── response_formatter.py  # Response formatting
│   └── error_handler.py   # Error handling
├── routes/                # API route implementations
│   ├── __init__.py
│   ├── deployments.py     # GET /api/v1/deployments
│   ├── deployments_test.py
│   ├── metrics.py         # GET /api/v1/metrics
│   ├── metrics_test.py
│   ├── health.py          # GET /api/v1/health
│   ├── health_test.py
│   ├── logs.py            # GET /api/v1/logs
│   └── logs_test.py
└── README.md              # This file
```

### Running Tests

```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest routes/deployments_test.py

# Run with coverage
uv run pytest --cov=. --cov-report=html
```

### Adding New Endpoints

1. Create a new route module in `routes/`
2. Implement the FastAPI router with proper models
3. Add comprehensive tests
4. Include the router in `app.py`
5. Update this README

## Data Files

The API uses JSON files in the `data/` directory:

- `config.json` - Application and environment configuration
- `deployments.json` - Deployment history and status
- `environments.json` - Environment definitions
- `logs.json` - Application logs
- `metrics.json` - Performance metrics
- `release_health.json` - Release health data
- `releases.json` - Release information

## Integration with MCP Servers

This API is designed to be consumed by MCP servers that provide AI assistant integration. The MCP server acts as a wrapper, making HTTP requests to this API and formatting responses for AI assistants.

Example MCP integration:
```python
import httpx

async def get_deployments_mcp_tool(application=None, environment=None):
    async with httpx.AsyncClient() as client:
        params = {}
        if application:
            params["application"] = application
        if environment:
            params["environment"] = environment
        
        response = await client.get(
            "http://localhost:8000/api/v1/deployments",
            params=params
        )
        return response.json()
```

## Production Deployment

### Using Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY . .

RUN pip install uv && uv sync --frozen

EXPOSE 8000
CMD ["./api-server"]
```

### Using systemd

```ini
[Unit]
Description=DevOps Dashboard API
After=network.target

[Service]
Type=simple
User=api
WorkingDirectory=/opt/devops-api
ExecStart=/opt/devops-api/api-server
Restart=always
Environment=HOST=0.0.0.0
Environment=PORT=8000

[Install]
WantedBy=multi-user.target
```

### Load Balancing

The API is stateless and can be easily load balanced:

```nginx
upstream devops_api {
    server 127.0.0.1:8000;
    server 127.0.0.1:8001;
    server 127.0.0.1:8002;
}

server {
    listen 80;
    location / {
        proxy_pass http://devops_api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Monitoring and Observability

### Health Checks

- **Liveness**: `GET /health`
- **Readiness**: `GET /health` (checks data file accessibility)

### Logging

The API uses Python's standard logging module. Configure log levels via environment:

```bash
export LOG_LEVEL=INFO
./api-server
```

### Metrics

Consider integrating with:
- Prometheus for metrics collection
- Grafana for visualization
- OpenTelemetry for distributed tracing

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

This project is part of the MCP servers basic examples and follows the same licensing terms.

---

**API Version**: 1.0.0  
**Last Updated**: 2024-01-15  
**Status**: Production Ready
