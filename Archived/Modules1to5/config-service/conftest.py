"""
conftest.py
-----------
Root-level pytest configuration.

Patches app.config.settings with dummy values so tests can import all
app modules without needing a real .env file or database connection.
"""

import os
import pytest


# Set required env vars BEFORE any app module is imported.
# This is evaluated at collection time, which is before any test runs.
os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost/config_service_test")
os.environ.setdefault("TEST_DATABASE_URL", "postgresql://test:test@localhost/config_service_test")
