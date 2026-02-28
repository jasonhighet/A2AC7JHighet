# Instructions for Prompt Generation
This document contains details necessary to create a prompt, which will later be used to create an implementation plan for a REST Web API. Please review the contents of this file and recommend a PROMPT that can be sent to an AI coding assistant for help with creating an implementation plan for this service. 

The prompt should:
- Ask the assistant to create a comprehensive plan that includes dependencies, file/folder structure, and architectural patterns.
- Recommend strict adherence to ALL of the details in this document.
- Strongly encourage the assistant to not add any additional dependencies without approval.
- Encourage the assistant to ask for more information if they need it.

---

# Technical Specifications: Config Service

## Tech Stack
- Language: Python 3.13.5 (Managed via uv)
- Web Framework: FastAPI 0.116.1
- Database: PostgreSQL (Native Windows install, no Docker)
- Database Adapter: psycopg2 2.9.10 (Strictly No ORM)
- Developer Tools: uv (for venv and dependencies), Makefile (standard Windows make)