"""Tests for OpenTelemetry tracer setup."""

import tempfile
from pathlib import Path

from src.observability.tracer import TracerSetup, initialize_tracing, shutdown_tracing


def test_tracer_setup_initialization():
    """Test that tracer setup initializes correctly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        setup = TracerSetup(output_dir=tmpdir, service_name="test-agent")
        tracer = setup.initialize()

        assert tracer is not None
        assert setup._provider is not None
        assert setup._exporter is not None

        setup.shutdown()


def test_tracer_creates_output_directory():
    """Test that tracer creates the output directory if it doesn't exist."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir) / "traces"
        assert not output_dir.exists()

        setup = TracerSetup(output_dir=str(output_dir), service_name="test-agent")
        setup.initialize()

        assert output_dir.exists()
        assert output_dir.is_dir()

        setup.shutdown()


def test_initialize_tracing_global_function():
    """Test the global initialize_tracing function."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tracer = initialize_tracing(output_dir=tmpdir, service_name="test-agent")

        assert tracer is not None

        shutdown_tracing()


def test_force_flush():
    """Test force flush functionality."""
    with tempfile.TemporaryDirectory() as tmpdir:
        setup = TracerSetup(output_dir=tmpdir, service_name="test-agent")
        setup.initialize()

        result = setup.force_flush()
        assert result is True

        setup.shutdown()


def test_shutdown_without_initialization():
    """Test that shutdown works even without initialization."""
    with tempfile.TemporaryDirectory() as tmpdir:
        setup = TracerSetup(output_dir=tmpdir, service_name="test-agent")
        # Don't call initialize()
        setup.shutdown()  # Should not raise an error


def test_multiple_tracer_setups_use_same_instance():
    """Test that get_tracer_setup returns the same instance."""
    from src.observability.tracer import get_tracer_setup

    with tempfile.TemporaryDirectory() as tmpdir:
        # Reset global state
        import src.observability.tracer as tracer_module

        tracer_module._tracer_setup = None

        setup1 = get_tracer_setup(output_dir=tmpdir)
        setup2 = get_tracer_setup(output_dir=tmpdir)

        assert setup1 is setup2

        # Cleanup
        shutdown_tracing()
