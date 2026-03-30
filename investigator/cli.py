#!/usr/bin/env python
"""CLI interface for the Investigator Agent.

This module provides a simple REPL (Read-Eval-Print Loop) interface for
interacting with the Investigator Agent from the command line.

Usage:
    python cli.py                  # Interactive conversation mode
    python cli.py --create-dataset # Create evaluation dataset in LangSmith
    python cli.py --eval           # Run evaluation on the dataset
"""

import argparse
import sys
from pathlib import Path

from langchain_core.messages import AIMessage, HumanMessage
from pydantic import ValidationError

# Ensure the project root is on sys.path so src.* imports resolve correctly
sys.path.insert(0, str(Path(__file__).parent))

from src.agent.graph import create_agent_graph
from src.utils.config import load_config


def print_welcome() -> None:
    """Print welcome message and usage instructions."""
    print("\n" + "=" * 60)
    print("  Investigator Agent CLI")
    print("=" * 60)
    print("\nAssess feature readiness: Development → UAT → Production\n")
    print("Type your question and press Enter.")
    print("Type 'exit' or 'quit' to end the session.\n")


def print_error(message: str) -> None:
    """Print a formatted error message.

    Args:
        message: Error message to display.
    """
    print(f"\n❌ Error: {message}\n")


def extract_text_from_response(content) -> str:
    """Extract plain text from an agent response content object.

    Handles both simple string responses and list-of-block responses
    that some models return.

    Args:
        content: The message content (str or list of blocks).

    Returns:
        Plain text string.
    """
    if isinstance(content, str):
        return content

    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                parts.append(block.get("text", ""))
            elif isinstance(block, str):
                parts.append(block)
        return "".join(parts)

    return str(content)


def run_conversation_mode() -> None:
    """Run the interactive REPL conversation loop."""
    print_welcome()

    # Load and validate configuration
    try:
        config = load_config()
        config.ensure_trace_directory_exists()
    except ValidationError as e:
        print_error("Configuration validation failed:")
        for error in e.errors():
            field = " -> ".join(str(loc) for loc in error["loc"])
            print(f"  • {field}: {error['msg']}")
        print(
            "\nPlease check your .env file or environment variables.\n"
            "See .env.example for required configuration."
        )
        sys.exit(1)
    except Exception as e:
        print_error(f"Failed to load configuration: {e}")
        sys.exit(1)

    # Initialise the agent graph
    try:
        graph = create_agent_graph(config)
    except Exception as e:
        print_error(f"Failed to initialise agent: {e}")
        sys.exit(1)

    # Initialise conversation persistence
    from src.agent.prompts import get_system_prompt
    from src.utils.conversation_persistence import ConversationPersistence

    conv_dir = Path("data/conversations")
    # Passing the tool-aware prompt version for persistence reference
    persistence = ConversationPersistence(
        directory=conv_dir,
        config=config,
        system_prompt=get_system_prompt(with_tools=True),
    )

    print(f"✓ Agent initialised (model: {config.model_name})")
    print(f"✓ Session ID: {persistence.conversation_id}")
    print(f"✓ Saving to: {persistence.get_filepath()}\n")

    # Maintain conversation state across turns in this session
    # Load initial state (will be empty for new session ID)
    state: dict = {"messages": persistence.load()}

    try:
        while True:
            try:
                user_input = input("You: ").strip()

                if user_input.lower() in ("exit", "quit", "q"):
                    print(f"\nSession saved to: {persistence.get_filepath()}")
                    print("Goodbye!\n")
                    break

                if not user_input:
                    continue

                # Append this turn's user message and invoke the graph
                input_state = {
                    "messages": list(state["messages"]) + [HumanMessage(content=user_input)]
                }

                for event in graph.stream(input_state):
                    for node_name, node_output in event.items():
                        if node_name == "agent" and "messages" in node_output:
                            for msg in node_output["messages"]:
                                if isinstance(msg, AIMessage):
                                    text = extract_text_from_response(msg.content)
                                    if text:
                                        print(f"\nAgent: {text}\n")

                        # Keep local state up to date with accumulated messages
                        if "messages" in node_output:
                            state["messages"] = (
                                input_state["messages"] + list(node_output["messages"])
                            )
                            input_state["messages"] = state["messages"]

                # Save session to disk after each turn
                persistence.save(state["messages"])

            except KeyboardInterrupt:
                print("\n\nGoodbye!\n")
                break
            except Exception as e:
                print_error(f"An error occurred: {e}")
                continue

    finally:
        pass  # Future: flush traces here in Step 4


def parse_args() -> argparse.Namespace:
    """Parse command line arguments.

    Returns:
        Parsed arguments namespace.
    """
    parser = argparse.ArgumentParser(
        description="Investigator Agent CLI — assess feature readiness"
    )

    parser.add_argument(
        "--eval",
        action="store_true",
        help="Run evaluation mode (evaluates agent on test dataset)",
    )

    parser.add_argument(
        "--create-dataset",
        action="store_true",
        help="Create/update evaluation dataset in LangSmith",
    )

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    if args.create_dataset:
        # Evaluation scaffolding added in Step 6
        print("Dataset creation will be available in Step 6.")
        sys.exit(0)

    if args.eval:
        # Evaluation scaffolding added in Step 6
        print("Evaluation mode will be available in Step 6.")
        sys.exit(0)

    run_conversation_mode()
