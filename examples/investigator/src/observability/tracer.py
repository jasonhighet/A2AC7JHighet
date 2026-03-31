"""OpenTelemetry tracer setup and configuration.

Initializes the OpenTelemetry tracing infrastructure for the agent.
"""

from typing import Optional

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from src.observability.exporter import JSONSpanExporter


class TracerSetup:
    """Sets up and manages OpenTelemetry tracing."""

    def __init__(
        self,
        output_dir: str = "traces",
        service_name: str = "investigator-agent",
        conversation_id: Optional[str] = None,
    ):
        """Initialize the tracer setup.

        Args:
            output_dir: Directory to write trace JSON files
            service_name: Name of the service for trace identification
            conversation_id: Conversation ID for linking traces to conversations
        """
        self.output_dir = output_dir
        self.service_name = service_name
        self.conversation_id = conversation_id
        self._provider: Optional[TracerProvider] = None
        self._exporter: Optional[JSONSpanExporter] = None

    def initialize(self) -> trace.Tracer:
        """Initialize OpenTelemetry tracing and return a tracer.

        Returns:
            Configured tracer instance
        """
        # Create resource with service name
        resource = Resource.create({"service.name": self.service_name})

        # Create trace provider
        self._provider = TracerProvider(resource=resource)

        # Create JSON exporter with conversation_id
        self._exporter = JSONSpanExporter(
            output_dir=self.output_dir, conversation_id=self.conversation_id
        )

        # Add batch span processor
        processor = BatchSpanProcessor(self._exporter)
        self._provider.add_span_processor(processor)

        # Set as global trace provider
        trace.set_tracer_provider(self._provider)

        # Return tracer
        return trace.get_tracer(__name__)

    def shutdown(self) -> None:
        """Shutdown the tracer and flush any remaining spans."""
        if self._provider:
            self._provider.shutdown()

    def force_flush(self, timeout_millis: int = 30000) -> bool:
        """Force flush any buffered spans.

        Args:
            timeout_millis: Timeout in milliseconds

        Returns:
            True if successful, False otherwise
        """
        if self._provider:
            return self._provider.force_flush(timeout_millis)
        return False


# Global tracer instance
_tracer_setup: Optional[TracerSetup] = None


def get_tracer_setup(
    output_dir: str = "traces",
    service_name: str = "investigator-agent",
    conversation_id: Optional[str] = None,
) -> TracerSetup:
    """Get or create the global tracer setup.

    Args:
        output_dir: Directory to write trace JSON files
        service_name: Name of the service for trace identification
        conversation_id: Conversation ID for linking traces to conversations

    Returns:
        Global tracer setup instance
    """
    global _tracer_setup
    if _tracer_setup is None:
        _tracer_setup = TracerSetup(
            output_dir=output_dir,
            service_name=service_name,
            conversation_id=conversation_id,
        )
    return _tracer_setup


def initialize_tracing(
    output_dir: str = "traces",
    service_name: str = "investigator-agent",
    conversation_id: Optional[str] = None,
) -> trace.Tracer:
    """Initialize OpenTelemetry tracing.

    Args:
        output_dir: Directory to write trace JSON files
        service_name: Name of the service for trace identification
        conversation_id: Conversation ID for linking traces to conversations

    Returns:
        Configured tracer instance
    """
    setup = get_tracer_setup(
        output_dir=output_dir,
        service_name=service_name,
        conversation_id=conversation_id,
    )
    return setup.initialize()


def shutdown_tracing() -> None:
    """Shutdown tracing and flush remaining spans."""
    global _tracer_setup
    if _tracer_setup:
        _tracer_setup.shutdown()
        _tracer_setup = None


def force_flush_traces(timeout_millis: int = 30000) -> bool:
    """Force flush any buffered traces.

    Args:
        timeout_millis: Timeout in milliseconds

    Returns:
        True if successful, False otherwise
    """
    global _tracer_setup
    if _tracer_setup:
        return _tracer_setup.force_flush(timeout_millis)
    return False
