from typing import List, Optional
from .models import Message, Conversation
from .provider import LLMProvider
from .persistence import FilePersistence
from .config import settings
from .tools import ToolRegistry, default_registry
from .observability import tracer
from .context import ContextManager

class DetectiveAgent:
    def __init__(
        self, 
        provider: LLMProvider, 
        persistence: FilePersistence, 
        system_prompt: Optional[str] = None,
        registry: Optional[ToolRegistry] = None,
        context_manager: Optional[ContextManager] = None
    ):
        self.provider = provider
        self.persistence = persistence
        self.system_prompt = system_prompt or settings.system_prompt
        self.registry = registry or default_registry
        self.context_manager = context_manager or ContextManager(max_tokens=settings.max_context_tokens)

    async def send_message(self, content: str, conversation_id: Optional[str] = None) -> Conversation:
        with tracer.start_as_current_span("send_message") as span:
            if conversation_id:
                conversation = self.persistence.load(conversation_id)
                if not conversation:
                    raise ValueError(f"Conversation {conversation_id} not found.")
            else:
                conversation = Conversation(system_prompt=self.system_prompt)
            
            # Link trace_id to conversation metadata
            trace_id = format(span.get_span_context().trace_id, '032x')
            conversation.metadata["last_trace_id"] = trace_id
            
            user_message = Message(role="user", content=content)
            conversation.messages.append(user_message)
            
            # Tool Loop
            max_iterations = 10
            iterations = 0
            with tracer.start_as_current_span("tool_loop") as loop_span:
                while iterations < max_iterations:
                    iterations += 1
                    # Apply Context Management
                    with tracer.start_as_current_span("context_management") as ctx_span:
                        messages_to_send = self.context_manager.get_truncated_messages(conversation)
                        ctx_span.set_attribute("context.original_count", len(conversation.messages))
                        ctx_span.set_attribute("context.truncated_count", len(messages_to_send))

                    # Get tool definitions
                    tools = self.registry.get_definitions() if self.registry else None
                    
                    # Call provider
                    with tracer.start_as_current_span("provider_call") as prov_span:
                        response_message = await self.provider.complete(
                            messages_to_send, 
                            conversation.system_prompt,
                            tools=tools
                        )
                    conversation.messages.append(response_message)
                    
                    # If no tool calls, we're done
                    if not response_message.tool_calls:
                        break
                    
                    # Execute tool calls
                    for tool_call in response_message.tool_calls:
                        with tracer.start_as_current_span("execute_tool") as tool_span:
                            tool_span.set_attribute("tool.name", tool_call.name)
                            result = await self.registry.execute(tool_call)
                            result_message = Message(
                                role="tool",
                                content=result.content,
                                tool_call_id=result.tool_call_id
                            )
                            conversation.messages.append(result_message)
                            tool_span.set_attribute("tool.success", result.success)
            
            self.persistence.save(conversation)
            return conversation
