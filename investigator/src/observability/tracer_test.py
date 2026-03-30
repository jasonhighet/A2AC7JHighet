"""Unit tests for the OpenTelemetry tracing setup."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from opentelemetry import trace

from src.observability.tracer import (
    TracerSetup,
    shutdown_tracing,
    force_flush_traces,
)


@pytest.fixture(autouse=True)
def cleanup_tracing():
    """Ensure tracing is shut down after each test."""
    yield
    shutdown_tracing()


def test_tracer_setup_initialization(tmp_path):
    """TracerSetup initializes the provider and exporter correctly."""
    output_dir = tmp_path / "traces"
    setup = TracerSetup(
        output_dir=str(output_dir),
        service_name="test-service",
        conversation_id="conv_test_123",
        use_batch_processor=False
    )
    
    tracer = setup.initialize(set_global=False)
    assert isinstance(tracer, trace.Tracer)
    assert setup._provider is not None
    assert setup._exporter is not None


def test_tracer_setup_flush_writes_to_disk(tmp_path):
    """TracerSetup.force_flush causes the JSON exporter to write spans to disk."""
    output_dir = tmp_path / "traces"
    conv_id = "conv_20260330_123456_abcde"
    
    setup = TracerSetup(
        output_dir=str(output_dir),
        service_name="test-service",
        conversation_id=conv_id,
        use_batch_processor=False
    )
    tracer = setup.initialize(set_global=False)

    # Start and end a span using THIS tracer
    with tracer.start_as_current_span("test-span") as span:
        span.set_attribute("test_attr", "test_value")

    # Flush traces to disk using the instance
    success = setup.force_flush()
    assert success is True

    # Verify a trace file was created
    trace_files = list(output_dir.glob("trace_*.json"))
    assert len(trace_files) >= 1
    
    # Verify content
    with open(trace_files[0], "r", encoding="utf-8") as f:
        data = json.load(f)
        assert data["conversation_id"] == conv_id
        assert len(data["spans"]) >= 1
        assert data["spans"][0]["name"] == "test-span"
        assert data["spans"][0]["attributes"]["test_attr"] == "test_value"
