"""LangChain callback handler for OpenTelemetry tracing.

Captures and records spans for LLM calls, tool execution, and chain
invocations within the agent graph.
"""

import logging
from typing import Any, Dict, List, Optional

from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.outputs import LLMResult
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode

logger = logging.getLogger(__name__)


class OpenTelemetryCallbackHandler(BaseCallbackHandler):
    """LangChain callback handler that emits OpenTelemetry spans."""

    def __init__(self, tracer: trace.Tracer, conversation_id: str):
        """Initialise the callback handler.

        Args:
            tracer: Configured OpenTelemetry tracer.
            conversation_id: Unique ID to correlate spans.
        """
        self.tracer = tracer
        self.conversation_id = conversation_id
        self._spans: Dict[str, Any] = {}

    def on_llm_start(
        self, serialized: Dict[str, Any], prompts: List[str], **kwargs: Any
    ) -> None:
        """Called when LLM begins execution."""
        run_id = kwargs.get("run_id")
        if not run_id:
            return

        model_name = "unknown"
        if serialized and "id" in serialized:
            model_name = serialized.get("id", ["unknown"])[-1]

        # Start a span for the LLM call
        span = self.tracer.start_span(
            name="llm.call",
            attributes={
                "conversation_id": self.conversation_id,
                "model_name": model_name,
                "prompt_count": len(prompts),
            },
        )
        self._spans[str(run_id)] = span

    def on_llm_end(self, response: LLMResult, **kwargs: Any) -> None:
        """Called when LLM finishes execution."""
        run_id = kwargs.get("run_id")
        if not run_id or str(run_id) not in self._spans:
            return

        span = self._spans[str(run_id)]

        # Capture token usage if present
        if response.llm_output:
            usage = response.llm_output.get("usage", {})
            if usage:
                span.set_attributes({
                    "prompt_tokens": usage.get("input_tokens", 0),
                    "completion_tokens": usage.get("output_tokens", 0),
                    "total_tokens": usage.get("total_tokens", 0),
                })

        span.set_status(Status(StatusCode.OK))
        span.end()
        del self._spans[str(run_id)]

    def on_llm_error(self, error: Exception, **kwargs: Any) -> None:
        """Called when LLM errors."""
        run_id = kwargs.get("run_id")
        if not run_id or str(run_id) not in self._spans:
            return

        span = self._spans[str(run_id)]
        span.set_status(Status(StatusCode.ERROR, str(error)))
        span.record_exception(error)
        span.end()
        del self._spans[str(run_id)]

    def on_chain_start(
        self, serialized: Dict[str, Any], inputs: Dict[str, Any], **kwargs: Any
    ) -> None:
        """Called when a chain (or graph) starts running."""
        run_id = kwargs.get("run_id")
        if not run_id:
            return

        # Determine node/chain name
        chain_name = "unknown"
        if serialized and "id" in serialized:
            chain_name = serialized.get("id", ["unknown"])[-1]

        # Extract user message if prominent
        user_message = None
        if "messages" in inputs and inputs["messages"]:
            last_msg = inputs["messages"][-1]
            if hasattr(last_msg, "content"):
                user_message = str(last_msg.content)

        span = self.tracer.start_span(
            name=f"chain.{chain_name}",
            attributes={
                "conversation_id": self.conversation_id,
                "chain_type": chain_name,
            },
        )

        if user_message:
            span.set_attribute("user_message", user_message[:500])

        self._spans[str(run_id)] = span

    def on_chain_end(self, outputs: Dict[str, Any], **kwargs: Any) -> None:
        """Called when a chain finishes running."""
        run_id = kwargs.get("run_id")
        if not run_id or str(run_id) not in self._spans:
            return

        span = self._spans[str(run_id)]

        # Extract final agent response
        if "messages" in outputs and outputs["messages"]:
            last_msg = outputs["messages"][-1]
            if hasattr(last_msg, "content"):
                span.set_attribute("agent_response", str(last_msg.content)[:1000])

        span.set_status(Status(StatusCode.OK))
        span.end()
        del self._spans[str(run_id)]

    def on_chain_error(self, error: Exception, **kwargs: Any) -> None:
        """Called when a chain errors."""
        run_id = kwargs.get("run_id")
        if not run_id or str(run_id) not in self._spans:
            return

        span = self._spans[str(run_id)]
        span.set_status(Status(StatusCode.ERROR, str(error)))
        span.record_exception(error)
        span.end()
        del self._spans[str(run_id)]

    def on_tool_start(
        self, serialized: Dict[str, Any], input_str: str, **kwargs: Any
    ) -> None:
        """Called when a tool execution starts."""
        run_id = kwargs.get("run_id")
        if not run_id:
            return

        tool_name = serialized.get("name", "unknown_tool") if serialized else "unknown_tool"

        span = self.tracer.start_span(
            name=f"tool.{tool_name}",
            attributes={
                "conversation_id": self.conversation_id,
                "tool_name": tool_name,
                "tool_input": input_str[:500],
            },
        )
        self._spans[str(run_id)] = span

    def on_tool_end(self, output: str, **kwargs: Any) -> None:
        """Called when a tool execution finishes."""
        run_id = kwargs.get("run_id")
        if not run_id or str(run_id) not in self._spans:
            return

        span = self._spans[str(run_id)]
        span.set_attributes({
            "tool_output": str(output)[:1000],
            "success": True,
        })
        span.set_status(Status(StatusCode.OK))
        span.end()
        del self._spans[str(run_id)]

    def on_tool_error(self, error: Exception, **kwargs: Any) -> None:
        """Called when a tool errors."""
        run_id = kwargs.get("run_id")
        if not run_id or str(run_id) not in self._spans:
            return

        span = self._spans[str(run_id)]
        span.set_attributes({
            "success": False,
            "error_message": str(error),
        })
        span.set_status(Status(StatusCode.ERROR, str(error)))
        span.record_exception(error)
        span.end()
        del self._spans[str(run_id)]
