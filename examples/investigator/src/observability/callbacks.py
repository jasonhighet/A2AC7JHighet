"""LangChain callback handler for OpenTelemetry tracing.

Captures spans for LangGraph agent operations, LLM calls, and tool invocations.
"""

from typing import Any, Dict, List

from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.outputs import LLMResult
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode


class OpenTelemetryCallbackHandler(BaseCallbackHandler):
    """LangChain callback handler that emits OpenTelemetry spans."""

    def __init__(self, tracer: trace.Tracer, conversation_id: str):
        """Initialize the callback handler.

        Args:
            tracer: OpenTelemetry tracer instance
            conversation_id: Unique identifier for the conversation
        """
        self.tracer = tracer
        self.conversation_id = conversation_id
        self._spans: Dict[str, Any] = {}

    def on_llm_start(
        self, serialized: Dict[str, Any], prompts: List[str], **kwargs: Any
    ) -> None:
        """Called when LLM starts running.

        Args:
            serialized: Serialized LLM configuration
            prompts: List of prompts being sent to LLM
            **kwargs: Additional keyword arguments
        """
        run_id = kwargs.get("run_id")
        if not run_id:
            return

        # Handle None serialized
        model_name = "unknown"
        if serialized and "id" in serialized:
            model_name = serialized.get("id", ["unknown"])[-1]

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
        """Called when LLM ends running.

        Args:
            response: LLM response
            **kwargs: Additional keyword arguments
        """
        run_id = kwargs.get("run_id")
        if not run_id or str(run_id) not in self._spans:
            return

        span = self._spans[str(run_id)]

        # Extract token usage if available
        if response.llm_output:
            usage = response.llm_output.get("usage", {})
            if usage:
                span.set_attributes(
                    {
                        "prompt_tokens": usage.get("input_tokens", 0),
                        "completion_tokens": usage.get("output_tokens", 0),
                        "total_tokens": usage.get("input_tokens", 0)
                        + usage.get("output_tokens", 0),
                    }
                )

        span.set_status(Status(StatusCode.OK))
        span.end()
        del self._spans[str(run_id)]

    def on_llm_error(self, error: Exception, **kwargs: Any) -> None:
        """Called when LLM errors.

        Args:
            error: The error that occurred
            **kwargs: Additional keyword arguments
        """
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
        """Called when a chain starts running.

        Args:
            serialized: Serialized chain configuration
            inputs: Chain inputs
            **kwargs: Additional keyword arguments
        """
        run_id = kwargs.get("run_id")
        if not run_id:
            return

        # Determine chain type (handle None serialized)
        chain_name = "unknown"
        if serialized and "id" in serialized:
            chain_name = serialized.get("id", ["unknown"])[-1]

        # Extract user message if present (convert to string to avoid type errors)
        user_message = None
        if "messages" in inputs and inputs["messages"]:
            last_msg = inputs["messages"][-1]
            if hasattr(last_msg, "content"):
                content = last_msg.content
                # Ensure content is a string
                user_message = str(content) if not isinstance(content, str) else content

        span = self.tracer.start_span(
            name=f"chain.{chain_name}",
            attributes={
                "conversation_id": self.conversation_id,
                "chain_type": chain_name,
            },
        )

        if user_message:
            span.set_attribute("user_message", user_message)

        self._spans[str(run_id)] = span

    def on_chain_end(self, outputs: Dict[str, Any], **kwargs: Any) -> None:
        """Called when a chain ends running.

        Args:
            outputs: Chain outputs
            **kwargs: Additional keyword arguments
        """
        run_id = kwargs.get("run_id")
        if not run_id or str(run_id) not in self._spans:
            return

        span = self._spans[str(run_id)]

        # Extract agent response if present (convert to string to avoid type errors)
        if "messages" in outputs and outputs["messages"]:
            last_msg = outputs["messages"][-1]
            if hasattr(last_msg, "content"):
                content = last_msg.content
                # Ensure content is a string
                agent_response = (
                    str(content) if not isinstance(content, str) else content
                )
                span.set_attribute("agent_response", agent_response)

        span.set_status(Status(StatusCode.OK))
        span.end()
        del self._spans[str(run_id)]

    def on_chain_error(self, error: Exception, **kwargs: Any) -> None:
        """Called when a chain errors.

        Args:
            error: The error that occurred
            **kwargs: Additional keyword arguments
        """
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
        """Called when a tool starts running.

        Args:
            serialized: Serialized tool configuration
            input_str: Tool input string
            **kwargs: Additional keyword arguments
        """
        run_id = kwargs.get("run_id")
        if not run_id:
            return

        # Handle None serialized
        tool_name = "unknown_tool"
        if serialized and "name" in serialized:
            tool_name = serialized.get("name", "unknown_tool")

        span = self.tracer.start_span(
            name=f"tool.{tool_name}",
            attributes={
                "conversation_id": self.conversation_id,
                "tool_name": tool_name,
                "tool_input": input_str[:500],  # Truncate long inputs
            },
        )
        self._spans[str(run_id)] = span

    def on_tool_end(self, output: str, **kwargs: Any) -> None:
        """Called when a tool ends running.

        Args:
            output: Tool output (may be a string or ToolMessage object)
            **kwargs: Additional keyword arguments
        """
        run_id = kwargs.get("run_id")
        if not run_id or str(run_id) not in self._spans:
            return

        span = self._spans[str(run_id)]

        # Convert output to string (it might be a ToolMessage object)
        output_str = str(output)

        # Truncate long outputs for span attributes
        truncated_output = output_str[:1000] if len(output_str) > 1000 else output_str
        span.set_attributes(
            {
                "tool_output": truncated_output,
                "success": True,
            }
        )

        span.set_status(Status(StatusCode.OK))
        span.end()
        del self._spans[str(run_id)]

    def on_tool_error(self, error: Exception, **kwargs: Any) -> None:
        """Called when a tool errors.

        Args:
            error: The error that occurred
            **kwargs: Additional keyword arguments
        """
        run_id = kwargs.get("run_id")
        if not run_id or str(run_id) not in self._spans:
            return

        span = self._spans[str(run_id)]
        span.set_attributes(
            {
                "success": False,
                "error_message": str(error),
            }
        )
        span.set_status(Status(StatusCode.ERROR, str(error)))
        span.record_exception(error)
        span.end()
        del self._spans[str(run_id)]
