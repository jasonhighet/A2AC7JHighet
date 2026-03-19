from typing import List, Optional
from .models import Message, Conversation
from .provider import LLMProvider
from .persistence import FilePersistence

class DetectiveAgent:
    def __init__(self, provider: LLMProvider, persistence: FilePersistence, system_prompt: Optional[str] = None):
        self.provider = provider
        self.persistence = persistence
        self.system_prompt = system_prompt or "You are a Detective Agent. Your goal is to investigate software releases and assess risks."

    async def send_message(self, content: str, conversation_id: Optional[str] = None) -> Conversation:
        if conversation_id:
            conversation = self.persistence.load(conversation_id)
            if not conversation:
                raise ValueError(f"Conversation {conversation_id} not found.")
        else:
            conversation = Conversation(system_prompt=self.system_prompt)
        
        user_message = Message(role="user", content=content)
        conversation.messages.append(user_message)
        
        # In Step 1, we just call the provider directly (no tool loop yet)
        # Note: In a real scenario, we might want to manage the context window here
        response_message = await self.provider.complete(conversation.messages, conversation.system_prompt)
        conversation.messages.append(response_message)
        
        self.persistence.save(conversation)
        return conversation
