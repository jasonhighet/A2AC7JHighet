import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence, Optional
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode
from opentelemetry.sdk.trace import TracerProvider, ReadableSpan
from opentelemetry.sdk.trace.export import SpanExporter, SpanExportResult, SimpleSpanProcessor

class JsonFileSpanExporter(SpanExporter):
    def __init__(self, directory: str = ".traces"):
        self.directory = Path(directory)
        self.directory.mkdir(exist_ok=True, parents=True)

    def export(self, spans: Sequence[ReadableSpan]) -> SpanExportResult:
        self.directory.mkdir(exist_ok=True, parents=True) # Ensure it exists
        for span in spans:
            trace_id = format(span.context.trace_id, '032x')
            trace_file = self.directory / f"trace_{trace_id}.json"
            
            span_data = {
                "name": span.name,
                "context": {
                    "trace_id": trace_id,
                    "span_id": format(span.context.span_id, '016x'),
                    "parent_id": format(span.parent.span_id, '016x') if span.parent else None,
                },
                "start_time": datetime.fromtimestamp(span.start_time / 1e9, tz=timezone.utc).isoformat(),
                "end_time": datetime.fromtimestamp(span.end_time / 1e9, tz=timezone.utc).isoformat(),
                "attributes": dict(span.attributes),
                "status": {
                    "status_code": span.status.status_code.name,
                    "description": span.status.description or "",
                },
            }
            
            try:
                if trace_file.exists():
                    with open(trace_file, "r+", encoding="utf-8") as f:
                        try:
                            data = json.load(f)
                        except json.JSONDecodeError:
                            data = []
                        data.append(span_data)
                        f.seek(0)
                        json.dump(data, f, indent=2)
                        f.truncate()
                else:
                    with open(trace_file, "w", encoding="utf-8") as f:
                        json.dump([span_data], f, indent=2)
            except Exception as e:
                print(f"Error exporting span: {e}")
                return SpanExportResult.FAILURE
                
        return SpanExportResult.SUCCESS

    def shutdown(self) -> None:
        pass

def setup_tracing():
    provider = TracerProvider()
    processor = SimpleSpanProcessor(JsonFileSpanExporter())
    provider.add_span_processor(processor)
    trace.set_tracer_provider(provider)

tracer = trace.get_tracer("detective-agent")
