# HyprCourse Project

A course project exploring AI-assisted software engineering practices, including meta-prompting, implementation planning, and code generation in a native Windows development environment.

## Project Goals

- Practice structured AI-assisted development workflows (plan → prompt → implement → reflect)
- Build production-quality REST APIs without shortcuts (no ORMs, pinned dependencies, full test coverage)
- Maintain a journal of prompts, tools, costs, and reflections as a learning record

## Services

| Service | Description | Path |
|---|---|---|
| `config-service` | Centralized configuration management REST API | [`config-service/`](./config-service/) |

## Prompt Artefacts

The `Prompts/` folder contains the AI prompts and plans generated during the course:

## Journal

See [`JOURNAL.md`](./JOURNAL.md) for per-entry reflections on prompting strategies, tooling decisions, and lessons learned.

## Environment

- **OS**: Windows (native — no Docker, WSL, or Linux assumed)
- **Shell**: PowerShell
- **Package manager**: [`uv`](https://github.com/astral-sh/uv)
- **Language**: Python 3.13+
- **Database**: PostgreSQL (native Windows install)
