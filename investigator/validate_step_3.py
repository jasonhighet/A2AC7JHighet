import sys
import io
from pathlib import Path
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

# Add src to path
sys.path.insert(0, '.')

from src.agent.graph import create_agent_graph
from src.utils.config import load_config
from src.utils.conversation_persistence import ConversationPersistence

def validate_step_3():
    # Set stdout to utf-8 to avoid Windows encoding issues with Unicode
    if sys.stdout.encoding != 'utf-8':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

    config = load_config()
    graph = create_agent_graph(config)
    
    conv_dir = Path('data/conversations')
    conv_dir.mkdir(parents=True, exist_ok=True)
    
    persistence = ConversationPersistence(conv_dir, config, 'Step 3 Validation')
    
    print(f"Session ID: {persistence.conversation_id}")
    
    # Query that requires JIRA data AND Analysis data
    question = 'Is the Maintenance Scheduling feature ready for UAT? Tell me about its unit test results.'
    print(f"You: {question}\n")
    
    messages = [HumanMessage(content=question)]
    state = {"messages": messages}
    
    # Run the graph and collect ALL events until it finishes
    for event in graph.stream(state):
        for node, output in event.items():
            print(f"[Node: {node}]")
            node_msgs = output.get('messages', [])
            for msg in node_msgs:
                if hasattr(msg, 'tool_calls') and msg.tool_calls:
                    for tc in msg.tool_calls:
                        print(f"  Tool Call Requested: {tc['name']}({tc['args']})")
                elif isinstance(msg, ToolMessage):
                    print(f"  Tool Response Received (length: {len(str(msg.content))})")
                elif isinstance(msg, AIMessage) and msg.content:
                    print(f"  AI Content: {str(msg.content)}")
                
                # Update our tracking
                state["messages"].append(msg)

    # Verify persistence
    persistence.save(state["messages"])
    print(f"\nPersistence file exists: {persistence.filepath.exists()}")
    
    # Final check: AI should have found 100% pass rate for FEAT-MS-001 (feature1)
    # feature1/metrics/unit_test_results.json: total: 72, passed: 72, failed: 0
    ai_final = next((m.content for m in reversed(state["messages"]) if isinstance(m, AIMessage) and m.content), "")
    
    # Check for unit test numbers 72 and 0
    if "72" in str(ai_final) and "0" in str(ai_final) and ("pass" in str(ai_final).lower() or "ready" in str(ai_final).lower()):
        print("\nStep 3 Validation: SUCCESS (AI correctly analysed test metrics)")
    else:
        print("\nStep 3 Validation: FAILED (Final response did not contain expected analysis metrics)")
        print(f"Final AI Content for debugging: {ai_final}")

if __name__ == "__main__":
    validate_step_3()
