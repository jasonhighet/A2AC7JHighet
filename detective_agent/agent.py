from typing import List, Optional
from .models import Message, Conversation
from .provider import LLMProvider
from .persistence import FilePersistence
from .config import settings
from .tools import ToolRegistry, default_registry

class DetectiveAgent:
    def __init__(
        self, 
        provider: LLMProvider, 
        persistence: FilePersistence, 
        system_prompt: Optional[str] = None,
        registry: Optional[ToolRegistry] = None
    ):
        self.provider = provider
        self.persistence = persistence
        self.system_prompt = system_prompt or settings.system_prompt
        self.registry = registry or default_registry

    async def send_message(self, content: str, conversation_id: Optional[str] = None) -> Conversation:
        if conversation_id:
            conversation = self.persistence.load(conversation_id)
            if not conversation:
                raise ValueError(f"Conversation {conversation_id} not found.")
        else:
            conversation = Conversation(system_prompt=self.system_prompt)
        
        user_message = Message(role="user", content=content)
        conversation.messages.append(user_message)
        
        # Tool Loop
        while True:
            # Get tool definitions
            tools = self.registry.get_definitions() if self.registry else None
            
            # Call provider
            response_message = await self.provider.complete(
                conversation.messages, 
                conversation.system_prompt,
                tools=tools
            )
            conversation.messages.append(response_message)
            
            # If no tool calls, we're done
            if not response_message.tool_calls:
                break
            
            # Execute tool calls
            for tool_call in response_message.tool_calls:
                result = await self.registry.execute(tool_call)
                result_message = Message(
                    role="tool",
                    content=result.content,
                    tool_call_id=result.tool_call_id
                )
                conversation.messages.append(result_message)
            
            # Loop back to let the LLM process tool results
        
        self.persistence.save(conversation)
        return conversation
