import sys
import io
from pathlib import Path
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, SystemMessage

# Add src to path
sys.path.insert(0, '.')

from src.agent.graph import create_agent_graph
from src.utils.config import load_config
from src.utils.conversation_persistence import ConversationPersistence

def debug_step_3():
    # Set stdout to utf-8
    if sys.stdout.encoding != 'utf-8':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

    config = load_config()
    graph = create_agent_graph(config)
    
    question = 'Is the Maintenance Scheduling feature ready for UAT? Tell me about its unit test results.'
    print(f"You: {question}\n")
    
    state = {"messages": [HumanMessage(content=question)]}
    
    for event in graph.stream(state):
        for node, output in event.items():
            print(f"\n--- Node: {node} ---")
            msgs = output.get('messages', [])
            for i, msg in enumerate(msgs):
                print(f"Message {i} ({type(msg).__name__}):")
                if hasattr(msg, 'tool_calls') and msg.tool_calls:
                    print(f"  Tool Calls: {msg.tool_calls}")
                print(f"  Content: {repr(msg.content)[:200]}...")
            
            # Update state
            state["messages"].extend(msgs)

if __name__ == "__main__":
    debug_step_3()
