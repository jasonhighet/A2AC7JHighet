"""JSON trace exporter for OpenTelemetry.

Exports traces to human-readable JSON files for analysis and debugging.
One trace file per conversation, matching the conversation file format.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from opentelemetry.sdk.trace import ReadableSpan
from opentelemetry.sdk.trace.export import SpanExporter, SpanExportResult


class JSONSpanExporter(SpanExporter):
    """Exports spans to JSON files for human-readable trace analysis.

    Accumulates all spans for a conversation and writes them to a single file
    when flushed (typically at conversation end).
    """

    def __init__(
        self, output_dir: str = "traces", conversation_id: Optional[str] = None
    ):
        """Initialize the JSON span exporter.

        Args:
            output_dir: Directory to write trace JSON files
            conversation_id: Conversation ID for this exporter instance
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.conversation_id = conversation_id
        self._spans_buffer: List[Dict[str, Any]] = []
        self._start_time: Optional[datetime] = None

    def export(self, spans: Sequence[ReadableSpan]) -> SpanExportResult:
        """Export spans by buffering them for later flush.

        Args:
            spans: Sequence of spans to export

        Returns:
            SpanExportResult indicating success or failure
        """
        try:
            for span in spans:
                span_dict = self._span_to_dict(span)

                # Extract conversation_id from first span if not set
                if not self.conversation_id:
                    self.conversation_id = span_dict.get("attributes", {}).get(
                        "conversation_id", "unknown"
                    )

                # Track start time from first span
                if not self._start_time and span_dict.get("start_time"):
                    self._start_time = datetime.fromisoformat(
                        span_dict["start_time"].replace("Z", "+00:00")
                    )

                self._spans_buffer.append(span_dict)

            return SpanExportResult.SUCCESS
        except Exception as e:
            print(f"Error exporting spans: {e}")
            return SpanExportResult.FAILURE

    def force_flush(self, timeout_millis: int = 30000) -> bool:
        """Force flush any buffered spans to a single trace file.

        Args:
            timeout_millis: Timeout in milliseconds (unused)

        Returns:
            True if successful, False otherwise
        """
        try:
            if self._spans_buffer:
                self._write_trace_file()
            return True
        except Exception as e:
            print(f"Error flushing spans: {e}")
            return False

    def shutdown(self) -> None:
        """Shutdown the exporter and flush remaining spans."""
        self.force_flush()

    def _span_to_dict(self, span: ReadableSpan) -> Dict[str, Any]:
        """Convert a span to a dictionary.

        Args:
            span: Span to convert

        Returns:
            Dictionary representation of the span
        """
        # Convert timestamps from nanoseconds to ISO format
        start_time = datetime.fromtimestamp(span.start_time / 1e9).isoformat() + "Z"
        end_time = (
            datetime.fromtimestamp(span.end_time / 1e9).isoformat() + "Z"
            if span.end_time
            else None
        )

        # Calculate duration in milliseconds
        duration_ms = None
        if span.end_time:
            duration_ms = (span.end_time - span.start_time) / 1e6

        # Convert attributes to dict
        attributes = {}
        if span.attributes:
            for key, value in span.attributes.items():
                # Convert bytes to string for JSON serialization
                if isinstance(value, bytes):
                    attributes[key] = value.decode("utf-8", errors="replace")
                else:
                    attributes[key] = value

        # Convert events
        events = []
        if span.events:
            for event in span.events:
                event_dict = {
                    "name": event.name,
                    "timestamp": datetime.fromtimestamp(
                        event.timestamp / 1e9
                    ).isoformat()
                    + "Z",
                    "attributes": dict(event.attributes) if event.attributes else {},
                }
                events.append(event_dict)

        # Get parent span ID if exists
        parent_span_id = None
        if span.parent and span.parent.span_id:
            parent_span_id = format(span.parent.span_id, "016x")

        return {
            "span_id": format(span.context.span_id, "016x"),
            "trace_id": format(span.context.trace_id, "032x"),
            "parent_span_id": parent_span_id,
            "name": span.name,
            "start_time": start_time,
            "end_time": end_time,
            "duration_ms": duration_ms,
            "attributes": attributes,
            "events": events,
            "status": {
                "status_code": span.status.status_code.name,
                "description": span.status.description or "",
            },
        }

    def _write_trace_file(self) -> None:
        """Write all buffered spans to a single JSON file."""
        if not self._spans_buffer:
            return

        # Get conversation_id (should be set by now)
        conversation_id = self.conversation_id or "unknown"

        # Extract the short conversation ID for the filename
        # If conversation_id is like "conv_abc123", use just "abc123"
        # Otherwise use the full conversation_id
        if conversation_id.startswith("conv_"):
            short_id = conversation_id[5:]  # Remove "conv_" prefix
        else:
            short_id = conversation_id

        # Create filename matching conversation file format: trace_YYYYMMDD_HHMMSS_xxxxx.json
        timestamp_str = (
            self._start_time.strftime("%Y%m%d_%H%M%S")
            if self._start_time
            else datetime.now().strftime("%Y%m%d_%H%M%S")
        )
        filename = f"trace_{timestamp_str}_{short_id}.json"
        filepath = self.output_dir / filename

        # Calculate summary statistics
        total_duration_ms = sum(
            span.get("duration_ms", 0) or 0 for span in self._spans_buffer
        )

        # Count operations by type
        operation_counts = {}
        for span in self._spans_buffer:
            name = span["name"]
            operation_type = name.split(".")[0] if "." in name else "other"
            operation_counts[operation_type] = (
                operation_counts.get(operation_type, 0) + 1
            )

        # Build trace document matching conversation file structure
        trace_doc = {
            "conversation_id": conversation_id,
            "started_at": self._start_time.isoformat()
            if self._start_time
            else datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "summary": {
                "total_spans": len(self._spans_buffer),
                "total_duration_ms": round(total_duration_ms, 2),
                "operation_counts": operation_counts,
            },
            "spans": self._spans_buffer,
        }

        # Write to file
        with open(filepath, "w") as f:
            json.dump(trace_doc, f, indent=2)

        # Clear buffer
        self._spans_buffer = []
