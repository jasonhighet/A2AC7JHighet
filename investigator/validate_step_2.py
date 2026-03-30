import sys
import io
from pathlib import Path
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

# Add src to path
sys.path.insert(0, '.')

from src.agent.graph import create_agent_graph
from src.utils.config import load_config
from src.utils.conversation_persistence import ConversationPersistence

def validate_step_2():
    # Set stdout to utf-8 to avoid Windows encoding issues with Unicode
    if sys.stdout.encoding != 'utf-8':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

    config = load_config()
    graph = create_agent_graph(config)
    
    conv_dir = Path('data/conversations')
    conv_dir.mkdir(parents=True, exist_ok=True)
    
    persistence = ConversationPersistence(conv_dir, config, 'Step 2 Validation')
    
    print(f"Session ID: {persistence.conversation_id}")
    
    # Query that requires JIRA data
    question = 'Which features are currently in \"Production Ready\" status?'
    print(f"You: {question}\n")
    
    messages = [HumanMessage(content=question)]
    
    for event in graph.stream({"messages": messages}):
        for node, output in event.items():
            print(f"[Node: {node}]")
            node_msgs = output.get('messages', [])
            for msg in node_msgs:
                if hasattr(msg, 'tool_calls') and msg.tool_calls:
                    for tc in msg.tool_calls:
                        print(f"  Tool Call Requested: {tc['name']}")
                elif isinstance(msg, ToolMessage):
                    print(f"  Tool Response Received (length: {len(msg.content)})")
                elif isinstance(msg, AIMessage) and msg.content:
                    print(f"  AI Content: {str(msg.content)}")
                
                messages.append(msg)

    # Verify persistence
    persistence.save(messages)
    print(f"\nPersistence file exists: {persistence.filepath.exists()}")
    
    loaded = persistence.load()
    print(f"Successfully loaded {len(loaded)} messages from storage.")
    
    # Check if the AI actually listed the production ready features
    # Based on the data, 'Maintenance Scheduling' is Production Ready.
    ai_final = next((m.content for m in reversed(messages) if isinstance(m, AIMessage) and m.content), "")
    
    if "Maintenance Scheduling" in str(ai_final) or "PLAT-1523" in str(ai_final):
        print("\nStep 2 Validation: SUCCESS (AI correctly used JIRA data)")
    else:
        print("\nStep 2 Validation: PARTIAL (AI responded but didn't mention expected data)")

if __name__ == "__main__":
    validate_step_2()
