"""JSON trace exporter for OpenTelemetry.

This module provides a custom SpanExporter that buffers spans and writes them
to a structured JSON file on disk, matching our conversation persistence format.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from opentelemetry.sdk.trace import ReadableSpan
from opentelemetry.sdk.trace.export import SpanExporter, SpanExportResult

logger = logging.getLogger(__name__)


class JSONSpanExporter(SpanExporter):
    """Exports OpenTelemetry spans to local JSON files.

    Accumulates spans in a buffer and writes them to a timestamped file
    when flushed. Integrates with the conversation ID for easy correlation.
    """

    def __init__(self, output_dir: Path, conversation_id: Optional[str] = None):
        """Initialise the JSON span exporter.

        Args:
            output_dir: Directory where trace files will be stored.
            conversation_id: Optional ID to correlate traces with conversations.
        """
        self.output_dir = output_dir
        self.conversation_id = conversation_id
        self._spans_buffer: List[Dict[str, Any]] = []
        self._start_time: Optional[datetime] = None

        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def export(self, spans: Sequence[ReadableSpan]) -> SpanExportResult:
        """Buffer spans for later export."""
        try:
            for span in spans:
                span_dict = self._span_to_dict(span)
                self._spans_buffer.append(span_dict)
                
                if not self._start_time:
                    self._start_time = datetime.fromisoformat(
                        span_dict["start_time"].replace("Z", "+00:00")
                    )

            return SpanExportResult.SUCCESS
        except Exception as e:
            logger.error(f"Error buffering spans for export: {e}")
            return SpanExportResult.FAILURE

    def force_flush(self, timeout_millis: int = 30000) -> bool:
        """Write all buffered spans to a JSON file."""
        try:
            if self._spans_buffer:
                self._write_trace_file()
            return True
        except Exception as e:
            logger.error(f"Error flushing traces to disk: {e}")
            return False

    def shutdown(self) -> None:
        """Flush remaining spans and shutdown."""
        self.force_flush()

    def _span_to_dict(self, span: ReadableSpan) -> Dict[str, Any]:
        """Convert a ReadableSpan to a serialisable dictionary.

        Args:
            span: The OpenTelemetry span to convert.

        Returns:
            A dictionary containing the span's metadata, timing, and attributes.
        """
        # Convert timestamps (nanoseconds) to ISO format strings
        start_time = datetime.fromtimestamp(span.start_time / 1e9).isoformat() + "Z"
        end_time = (
            datetime.fromtimestamp(span.end_time / 1e9).isoformat() + "Z"
            if span.end_time
            else None
        )

        duration_ms = (
            (span.end_time - span.start_time) / 1e6 if span.end_time else None
        )

        # Convert attributes, handling non-serialisable types
        attributes = {}
        if span.attributes:
            for key, value in span.attributes.items():
                if isinstance(value, bytes):
                    attributes[key] = value.decode("utf-8", errors="replace")
                else:
                    attributes[key] = value

        # Convert events
        events = []
        if span.events:
            for event in span.events:
                events.append({
                    "name": event.name,
                    "timestamp": datetime.fromtimestamp(event.timestamp / 1e9).isoformat() + "Z",
                    "attributes": dict(event.attributes) if event.attributes else {},
                })

        return {
            "span_id": format(span.context.span_id, "016x"),
            "trace_id": format(span.context.trace_id, "032x"),
            "parent_span_id": (
                format(span.parent.span_id, "016x") if span.parent else None
            ),
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
        """Write buffered spans to a well-named JSON file."""
        if not self._spans_buffer:
            return

        conv_id = self.conversation_id or "unknown"
        short_id = conv_id[5:] if conv_id.startswith("conv_") else conv_id
        
        timestamp = (
            self._start_time or datetime.now()
        ).strftime("%Y%m%d_%H%M%S")
        
        filename = f"trace_{timestamp}_{short_id}.json"
        filepath = self.output_dir / filename

        # Compile trace document
        trace_doc = {
            "conversation_id": conv_id,
            "recorded_at": datetime.now().isoformat(),
            "summary": {
                "total_spans": len(self._spans_buffer),
                "total_duration_ms": sum(
                    s.get("duration_ms") or 0 for s in self._spans_buffer
                ),
            },
            "spans": self._spans_buffer,
        }

        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(trace_doc, f, indent=2)
            logger.debug(f"Exported trace to {filepath}")
        except OSError as e:
            logger.error(f"Failed to write trace file: {e}")
        finally:
            # Clear buffer after attempt (even if failed, to avoid memory leaks)
            self._spans_buffer = []
