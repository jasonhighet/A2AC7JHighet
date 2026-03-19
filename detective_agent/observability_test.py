import pytest
import os
import shutil
import json
from pathlib import Path
from opentelemetry import trace
from .observability import setup_tracing, tracer, JsonFileSpanExporter
from .agent import DetectiveAgent
from .provider import LLMStudioProvider
from .persistence import FilePersistence
import respx
from httpx import Response

@pytest.fixture(scope="module", autouse=True)
def init_tracing():
    setup_tracing()

@pytest.fixture
def temp_traces(tmp_path):
    trace_dir = tmp_path / ".traces"
    exporter = JsonFileSpanExporter(str(trace_dir))
    # We don't want to re-setup the global provider in tests if already done, 
    # but we can test the exporter directly.
    return trace_dir, exporter

@pytest.mark.asyncio
async def test_trace_generation(tmp_path):
    trace_dir = tmp_path / ".traces"
    # Create a local tracer and provider for testing
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import SimpleSpanProcessor
    provider = TracerProvider()
    exporter = JsonFileSpanExporter(str(trace_dir))
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    test_tracer = provider.get_tracer("test-tracer")
    
    with test_tracer.start_as_current_span("root") as root:
        trace_id = format(root.get_span_context().trace_id, '032x')
        with test_tracer.start_as_current_span("child"):
            pass
            
    # Check if file exists
    trace_file = trace_dir / f"trace_{trace_id}.json"
    assert trace_file.exists()
    
    with open(trace_file, "r") as f:
        spans = json.load(f)
        assert len(spans) == 2
        assert any(s["name"] == "root" for s in spans)
        assert any(s["name"] == "child" for s in spans)

@pytest.mark.asyncio
async def test_agent_instrumentation(tmp_path):
    # This test verifies that the agent generates traces into the default .traces dir
    # Note: depends on global setup_tracing()
    if os.path.exists(".traces"):
        shutil.rmtree(".traces")
        
    provider = LLMStudioProvider()
    persistence = FilePersistence(str(tmp_path))
    agent = DetectiveAgent(provider, persistence)
    
    with respx.mock:
        respx.post("http://localhost:1234/v1/chat/completions").mock(return_value=Response(200, json={
            "choices": [{"message": {"role": "assistant", "content": "Hello"}}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15}
        }))
        
        conv = await agent.send_message("Hi")
        trace_id = conv.metadata.get("last_trace_id")
        assert trace_id is not None
        
        # Wait a bit for SimpleSpanProcessor (though it's sync)
        trace_file = Path(".traces") / f"trace_{trace_id}.json"
        assert trace_file.exists()
        
        with open(trace_file, "r") as f:
            spans = json.load(f)
            # send_message -> tool_loop -> provider_call -> llm_completion
            assert any(s["name"] == "send_message" for s in spans)
            assert any(s["name"] == "llm_completion" for s in spans)
            
            # Check attributes
            llm_span = next(s for s in spans if s["name"] == "llm_completion")
            assert llm_span["attributes"]["llm.usage.total_tokens"] == 15
