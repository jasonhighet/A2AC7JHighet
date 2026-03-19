import tiktoken
import json
from typing import List, Optional
from .models import Message, Conversation

class ContextManager:
    """
    Manages the context window by counting tokens and truncating older messages if necessary.
    """
    def __init__(self, max_tokens: int = 4096, model: str = "gpt-3.5-turbo"):
        self.max_tokens = max_tokens
        # Use tiktoken to estimate tokens accurately for OpenAI-compatible models
        try:
            self.encoding = tiktoken.encoding_for_model(model)
        except (KeyError, ValueError):
            self.encoding = tiktoken.get_encoding("cl100k_base")

    def count_tokens(self, messages: List[Message], system_prompt: str) -> int:
        """
        Estimates the number of tokens in a conversation including system prompt and messages.
        This is an approximation based on the cl100k_base encoding.
        """
        num_tokens = 0
        # Estimate for system prompt
        num_tokens += len(self.encoding.encode(system_prompt)) + 4 # role, content markers
        
        for msg in messages:
            num_tokens += 4 # role, content markers
            if msg.content:
                num_tokens += len(self.encoding.encode(msg.content))
            if msg.tool_calls:
                for tc in msg.tool_calls:
                    num_tokens += len(self.encoding.encode(tc.name))
                    # Simplified arguments estimation
                    num_tokens += len(self.encoding.encode(json.dumps(tc.arguments)))
            if msg.tool_call_id:
                num_tokens += len(self.encoding.encode(msg.tool_call_id))
                
        return num_tokens

    def get_truncated_messages(self, conversation: Conversation) -> List[Message]:
        """
        Returns a list of messages from the conversation truncated to fit within max_tokens.
        Preserves the system prompt (outside the messages list) and as many recent messages as possible.
        """
        messages = list(conversation.messages) # Copy list
        
        # We must keep at least the last message if everything fits, 
        # or truncate from the beginning until it fits.
        while self.count_tokens(messages, conversation.system_prompt) > self.max_tokens:
            if len(messages) <= 1:
                # If even 1 message doesn't fit, we have to return it as-is or truncate its content.
                # For now, we keep at least the last message even if it exceeds the limit.
                break 
            messages.pop(0) # Remove oldest message
            
        return messages
