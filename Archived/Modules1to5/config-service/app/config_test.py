"""
app/config_test.py
------------------
Tests for Settings loading.
"""

import os
from unittest.mock import patch

import pytest


def test_settings_reads_database_url():
    from app.config import Settings

    with patch.dict(os.environ, {"DATABASE_URL": "postgresql://u:p@localhost/testdb"}):
        s = Settings()
        assert s.database_url == "postgresql://u:p@localhost/testdb"


def test_settings_defaults():
    from app.config import Settings

    with patch.dict(os.environ, {"DATABASE_URL": "postgresql://u:p@localhost/testdb"}):
        s = Settings()
        assert s.app_host == "127.0.0.1"
        assert s.app_port == 8000
