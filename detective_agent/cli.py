import asyncio
import sys
from .agent import DetectiveAgent
from .provider import LLMStudioProvider
from .persistence import FilePersistence

async def async_input(prompt: str) -> str:
    """Read input asynchronously to avoid blocking the loop."""
    return await asyncio.to_thread(input, prompt)

async def main():
    from .config import settings
    provider = LLMStudioProvider(base_url=settings.llm_base_url, model=settings.llm_model)
    persistence = FilePersistence()
    agent = DetectiveAgent(provider, persistence)
    
    print("Detective Agent CLI (Step 1)")
    print("Type 'exit' to quit. Type 'list' to see mapping. Type 'load <id>' to resume.")
    
    current_conversation_id = None
    
    while True:
        try:
            line = await async_input("\nYou: ")
            user_input = line.strip()
            
            if user_input.lower() == "exit":
                break
            if user_input.lower() == "list":
                convs = persistence.list_conversations()
                print(f"Conversations: {convs}")
                continue
            if user_input.lower().startswith("load "):
                parts = user_input.split(" ")
                if len(parts) > 1:
                    current_conversation_id = parts[1]
                    print(f"Switched to conversation {current_conversation_id}")
                continue
            
            conversation = await agent.send_message(user_input, current_conversation_id)
            current_conversation_id = conversation.id
            print(f"\nAgent: {conversation.messages[-1].content}")
            print(f"(Conversation ID: {conversation.id})")
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
