"""OpenTelemetry tracer setup and configuration.

Initialises the tracing infrastructure for the agent, linking spans to the
global tracer provider and a custom JSON exporter.
"""

import logging
from typing import Optional

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, SimpleSpanProcessor

from src.observability.exporter import JSONSpanExporter
from src.utils.config import load_config

logger = logging.getLogger(__name__)


class TracerSetup:
    """Manages the lifecycle of OpenTelemetry tracing."""

    def __init__(
        self,
        output_dir: str = "data/traces",
        service_name: str = "investigator-agent",
        conversation_id: Optional[str] = None,
        use_batch_processor: bool = True,
    ):
        """Initialise the tracer setup.

        Args:
            output_dir: Directory to write trace JSON files.
            service_name: Name of the service for trace metadata.
            conversation_id: Unique ID for this session/conversation.
            use_batch_processor: If True, uses BatchSpanProcessor (best for production).
                                 If False, uses SimpleSpanProcessor (best for tests).
        """
        self.output_dir = output_dir
        self.service_name = service_name
        self.conversation_id = conversation_id
        self.use_batch_processor = use_batch_processor
        self._provider: Optional[TracerProvider] = None
        self._exporter: Optional[JSONSpanExporter] = None

    def initialize(self, set_global: bool = True) -> trace.Tracer:
        """Initialise OpenTelemetry and return a tracer.

        Args:
            set_global: If True, sets this as the global tracer provider.

        Returns:
            A configured OpenTelemetry tracer.
        """
        # Create resource metadata
        resource = Resource.create({"service.name": self.service_name})
        
        # Create trace provider
        self._provider = TracerProvider(resource=resource)
        
        # Create JSON exporter
        from pathlib import Path
        output_path = Path(self.output_dir)
        self._exporter = JSONSpanExporter(
            output_dir=output_path,
            conversation_id=self.conversation_id
        )
        
        # Add span processor
        if self.use_batch_processor:
            processor = BatchSpanProcessor(self._exporter)
        else:
            processor = SimpleSpanProcessor(self._exporter)
            
        self._provider.add_span_processor(processor)
        
        # Set as global trace provider if requested
        if set_global:
            try:
                trace.set_tracer_provider(self._provider)
            except ValueError:
                # Already set, this is fine
                logger.debug("Tracer provider already set.")
        
        # Return tracer
        return self._provider.get_tracer(__name__)

    def shutdown(self) -> None:
        """Shutdown the tracer and flush buffered spans."""
        if self._provider:
            self._provider.shutdown()
            logger.debug("Tracer system shut down.")

    def force_flush(self, timeout_millis: int = 30000) -> bool:
        """Force flush all buffered spans to the exporter."""
        if self._provider:
            # First flush the provider/processors
            res = self._provider.force_flush(timeout_millis)
            
            # Then explicitly flush the exporter if it exists
            if self._exporter:
                self._exporter.force_flush(timeout_millis)
            
            return res
        return False


# Global tracer setup singleton for this process
_tracer_setup: Optional[TracerSetup] = None


def initialize_tracing(
    output_dir: str = "data/traces",
    service_name: str = "investigator-agent",
    conversation_id: Optional[str] = None,
) -> trace.Tracer:
    """Convenience function to start tracing globaly.

    Args:
        output_dir: Trace storage directory.
        service_name: Name of this agent service.
        conversation_id: ID for the current session.

    Returns:
        The configured tracer instance.
    """
    global _tracer_setup
    # Force a new setup if conversation_id or output_dir changes (e.g. in tests)
    if _tracer_setup is not None:
        if _tracer_setup.conversation_id != conversation_id or _tracer_setup.output_dir != output_dir:
            logger.debug("Tracing parameters changed, restarting tracer.")
            _tracer_setup.shutdown()
            _tracer_setup = None

    if _tracer_setup is None:
        _tracer_setup = TracerSetup(
            output_dir=output_dir,
            service_name=service_name,
            conversation_id=conversation_id,
        )
    return _tracer_setup.initialize()


def shutdown_tracing() -> None:
    """Shutdown the global tracing and flush all traces."""
    global _tracer_setup
    if _tracer_setup:
        _tracer_setup.shutdown()
        _tracer_setup = None


def force_flush_traces(timeout_millis: int = 30000) -> bool:
    """Force flush any buffered traces to disk."""
    global _tracer_setup
    if _tracer_setup:
        return _tracer_setup.force_flush(timeout_millis)
    return False
