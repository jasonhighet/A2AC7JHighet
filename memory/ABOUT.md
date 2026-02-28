# Project Memory: HyprCourse Config Service

## Project Name
**HyprCourse: Config Service**

## Description
A centralized configuration management system designed to provide dynamic, environment-specific settings to distributed applications. This project serves as a practical exploration of AI-assisted software engineering, focusing on high-quality REST API development using a "No-Shortcuts" architecture (Native Windows, Python 3.13, FastAPI, PostgreSQL via psycopg2, strictly no ORM).

## Domain Context: Centralized Configuration
In modern microservices architectures, managing configuration across multiple instances and environments (dev, staging, prod) is a common challenge. 
- **Centralization**: Provides a single source of truth for application settings.
- **Dynamic Updates**: Allows changing configuration at runtime without redeploying services.
- **Environment Awareness**: Scopes variables to specific environments or application instances.
- **Security**: Centralizes secrets management and access control.

## Target Personas
- **Application Developers**: Users who need to retrieve configuration values for their services via the REST API. They care about latency, reliability, and clear API contracts.
- **System Administrators / DevOps Engineers**: Users responsible for managing the configuration data (creating/updating apps, environments, and variables). They care about audit trails, bulk updates, and the Admin UI.
- **Security Officers**: Users focused on ensuring that sensitive configuration (secrets) is handled correctly and that access is restricted according to least privilege.

## Core Architectural Principles
- **No ORM**: Direct SQL usage via `psycopg2` for maximum control and performance.
- **Native Windows**: Developed and tested on Windows PowerShell, avoiding Linux-based abstractions (Docker/WSL).
- **Type Safety**: Heavy use of Python type hinting and Pydantic for request/response validation.
- **Test-Driven**: Comprehensive test coverage using `pytest`.
